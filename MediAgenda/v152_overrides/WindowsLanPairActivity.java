package com.mediagenda.app;

import android.app.Activity;
import android.app.AlertDialog;
import android.os.Bundle;
import android.os.Build;
import android.net.nsd.NsdManager;
import android.net.wifi.WifiManager;
import android.net.nsd.NsdServiceInfo;
import android.graphics.Color;
import android.graphics.Typeface;
import android.view.Gravity;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.BufferedWriter;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.IOException;
import java.net.ServerSocket;
import java.net.DatagramSocket;
import java.net.DatagramPacket;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.net.Inet4Address;
import java.net.NetworkInterface;
import java.net.InetAddress;
import java.nio.charset.StandardCharsets;
import java.security.SecureRandom;
import java.util.Enumeration;
import java.util.UUID;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Embedded Android <-> Windows discovery / approval demonstration.
 *
 * Does NOT read clinical app storage or transmit private data. This manually-enabled
 * proof-of-connection uses HTTP over local Wi-Fi with a six-digit displayed
 * code and manual consent. It is NOT secure enough for medical sync. A future
 * production protocol MUST authenticate and encrypt the data channel.
 */
public final class WindowsLanPairActivity extends Activity {
    private static final String TYPE = "_saudepratica-sync._tcp.";
    private static final String PROTO = "sp-pair-test-0";
    private static final int UDP_DISCOVERY_PORT = 43838;
    private static final String UDP_QUESTION = "SP_DISCOVER_1:";
    private static final String UDP_ANSWER = "SP_FOUND_1:";
    private static final int MAX_REQUEST = 1024;
    private volatile boolean running = false;
    private ServerSocket server;
    private NsdManager nsd;
    private NsdManager.RegistrationListener registration;
    private DatagramSocket udpDiscovery;
    private WifiManager.MulticastLock multicastLock;
    private TextView status, detail;
    private final ConcurrentHashMap<String, Pending> requests = new ConcurrentHashMap<>();
    private final SecureRandom random = new SecureRandom();
    private final int DARK = Color.rgb(7, 26, 38);
    private final int TEAL = Color.rgb(0, 190, 170);

    private static final class Pending {
        final String code;
        final long created = System.currentTimeMillis();
        volatile String state = "pending";
        Pending(String c) { code = c; }
    }

    private TextView text(String value, int size, boolean bold) {
        TextView view = new TextView(this);
        view.setText(value);
        view.setTextColor(Color.WHITE);
        view.setTextSize(size);
        view.setPadding(15, 15, 15, 15);
        if (bold) view.setTypeface(null, Typeface.BOLD);
        return view;
    }

    private Button button(String label, Runnable action) {
        Button view = new Button(this);
        view.setText(label);
        view.setAllCaps(false);
        view.setTextColor(Color.WHITE);
        view.setBackgroundTintList(android.content.res.ColorStateList.valueOf(Color.rgb(26,51,61)));
        view.setPadding(15,15,15,15);
        view.setOnClickListener(v -> action.run());
        return view;
    }

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        nsd = (NsdManager) getSystemService(NSD_SERVICE);
        ScrollView scroller = new ScrollView(this);
        int backdrop=getResources().getIdentifier(
            "saude_background","drawable",getPackageName());
        if(backdrop!=0) {
            scroller.setBackgroundResource(backdrop);
        } else scroller.setBackgroundColor(DARK);
        LinearLayout body = new LinearLayout(this);
        body.setOrientation(LinearLayout.VERTICAL);
        body.setPadding(24, 26, 24, 26);
        body.setBackgroundColor(Color.argb(170,7,26,38));
        scroller.addView(body);
        body.addView(text("SaúdePrática · Windows\nLigação Wi-Fi (teste)", 22, true));
        body.addView(text("Esta ligação faz parte da SaúdePrática. Torna o telemóvel visível "
                + "no Wi-Fi e confirma no Android o pedido feito pelo Windows.", 15, false));
        body.addView(text("Neste teste só é confirmado o emparelhamento. Ainda NÃO transfere medicação, perfis, consultas ou fotografias.", 16, true));
        body.addView(button("1 · Tornar visível no Wi-Fi", this::start));
        body.addView(button("2 · Parar / desligar", this::stop));
        status = text("Desligado. Liga o Wi-Fi e toca em «Tornar visível».", 16, true);
        body.addView(status);
        detail = text("No Windows, abre SaúdePrática → Opções → Sincronização. "
                + "O PC procura este telemóvel por mDNS e broadcast UDP. "
                + "Se não aparecer, utiliza o IP e a porta mostrados aqui.", 14, false);
        body.addView(detail);
        body.addView(text("SEGURANÇA: Esta experiência troca apenas um pedido de ligação e "
                + "um código. Não usa um canal cifrado e NÃO deve ser utilizada "
                + "para transmitir qualquer informação clínica.", 13, false));
        setContentView(scroller);
    }

    private void show(String text) {
        runOnUiThread(() -> { if (status != null) status.setText(text); });
    }

    private static String localAddress() {
        try {
            Enumeration<NetworkInterface> interfaces = NetworkInterface.getNetworkInterfaces();
            String fallback = "";
            while (interfaces.hasMoreElements()) {
                NetworkInterface iface = interfaces.nextElement();
                if (!iface.isUp() || iface.isLoopback()) continue;
                Enumeration<InetAddress> values = iface.getInetAddresses();
                while (values.hasMoreElements()) {
                    InetAddress ip = values.nextElement();
                    if (!(ip instanceof Inet4Address) || ip.isLoopbackAddress()) continue;
                    String value = ip.getHostAddress();
                    if (iface.getName().startsWith("wlan")) return value;
                    if (fallback.isEmpty()) fallback = value;
                }
            }
            return fallback.isEmpty() ? "IP indisponível" : fallback;
        } catch (Exception e) {
            return "IP indisponível";
        }
    }


    private void enableMulticastReception() {
        // Older Android releases require a lock even when the activity is
        // visible; newer ones manage foreground NSD automatically.
        try {
            WifiManager wifi=(WifiManager)getApplicationContext()
                .getSystemService(WIFI_SERVICE);
            if (wifi == null) return;
            multicastLock=wifi.createMulticastLock("SaudePratica-LAN-Link");
            multicastLock.setReferenceCounted(false);
            multicastLock.acquire();
        } catch (RuntimeException ignored) {
            multicastLock=null;
        }
    }

    private void beginUdpDiscovery(final int tcpPort) {
        // The Android is only discoverable after the user taps "Tornar
        // visível". This UDP channel answers a random nonce with its TCP
        // port and innocuous device label; it never touches clinical data.
        try {
            DatagramSocket listener=new DatagramSocket(null);
            listener.setReuseAddress(true);
            listener.bind(new InetSocketAddress("0.0.0.0",UDP_DISCOVERY_PORT));
            listener.setSoTimeout(1400);
            udpDiscovery=listener;
            new Thread(() -> {
                final byte[] input=new byte[256];
                while (running && !listener.isClosed()) {
                    try {
                        DatagramPacket question=new DatagramPacket(input,input.length);
                        listener.receive(question);
                        InetAddress from=question.getAddress();
                        if (!(from instanceof Inet4Address)
                                || !(from.isSiteLocalAddress() || from.isLinkLocalAddress())) {
                            continue;
                        }
                        String text=new String(question.getData(),
                            question.getOffset(),question.getLength(),
                            StandardCharsets.US_ASCII);
                        if (!text.matches("^SP_DISCOVER_1:[0-9a-f]{32}$")) {
                            continue;
                        }
                        String nonce=text.substring(UDP_QUESTION.length());
                        String model=Build.MODEL.replaceAll("[^a-zA-Z0-9 _-]", "")
                            .trim();
                        if (model.isEmpty()) model="Android";
                        String reply=UDP_ANSWER+nonce+":"+tcpPort+":"
                            +"SaúdePrática Android "+model;
                        byte[] output=reply.getBytes(StandardCharsets.UTF_8);
                        if (output.length>256) continue;
                        listener.send(new DatagramPacket(
                            output,output.length,from,question.getPort()));
                    } catch (java.net.SocketTimeoutException ignored) {
                    } catch (IOException e) {
                        if (running && !listener.isClosed()) {
                            show("Descoberta UDP interrompida. "
                                +"Continua disponível a ligação por IP.");
                        }
                        break;
                    }
                }
            }, "sp-core-lan-discovery").start();
        } catch (IOException e) {
            if (udpDiscovery!=null) udpDiscovery.close();
            udpDiscovery=null;
            show("UDP indisponível. mDNS e ligação por IP continuam disponíveis.");
        }
    }

    private synchronized void start() {
        if (running) { show("Já está visível. Espera o pedido do Windows."); return; }
        try {
            server = new ServerSocket(0);
            server.setSoTimeout(1300);
            running = true;
            final int port = server.getLocalPort();
            show("A iniciar descoberta...");
            new Thread(this::acceptLoop, "sp-core-lan-server").start();
            enableMulticastReception();
            beginUdpDiscovery(port);
            NsdServiceInfo info = new NsdServiceInfo();
            info.setServiceName("SaudePratica Ligacao " + Build.MODEL.replaceAll("[^a-zA-Z0-9 _-]", "").trim());
            info.setServiceType(TYPE);
            info.setPort(port);
            info.setAttribute("proto", PROTO);
            info.setAttribute("mode", "link-only");
            info.setAttribute("name", ("SaúdePrática Android · " + Build.MODEL).substring(
                0, Math.min(60, ("SaúdePrática Android · " + Build.MODEL).length())));
            registration = new NsdManager.RegistrationListener() {
                @Override public void onServiceRegistered(NsdServiceInfo registered) {
                    show("VISÍVEL · "+registered.getServiceName()+
                         "\nIP: "+localAddress()+"   Porta: "+port+
                         "\nAguardando pedido do Windows...");
                }
                @Override public void onRegistrationFailed(NsdServiceInfo entry, int code) {
                    show("mDNS falhou ("+code+"), mas a procura alternativa "
                        +"por UDP continua disponível.\n"
                        +"IP: "+localAddress()+" · Porta "+port);
                }
                @Override public void onServiceUnregistered(NsdServiceInfo entry) {
                    show("Desligado.");
                }
                @Override public void onUnregistrationFailed(NsdServiceInfo entry, int code) {
                    show("Erro ao desligar a descoberta: "+code);
                }
            };
            try {
                nsd.registerService(info,NsdManager.PROTOCOL_DNS_SD,registration);
            } catch (RuntimeException error) {
                registration=null;
                show("mDNS indisponível. Descoberta UDP ativa; alternativa "
                     +"manual IP: "+localAddress()+" · Porta "+port);
            }
        } catch (Exception e) {
            running = false;
            if (server != null) try { server.close(); } catch (IOException ignored) {}
            if (udpDiscovery!=null) udpDiscovery.close();
            udpDiscovery=null;
            if (multicastLock!=null) {
                try { if (multicastLock.isHeld()) multicastLock.release(); }
                catch (RuntimeException ignored) {}
                multicastLock=null;
            }
            show("Não foi possível abrir a ligação: "+e.getMessage());
        }
    }

    private synchronized void stop() {
        running = false;
        if (server != null) try { server.close(); } catch (IOException ignored) {}
        server = null;
        if (udpDiscovery != null) {
            udpDiscovery.close();
            udpDiscovery=null;
        }
        if (multicastLock != null) {
            try { if (multicastLock.isHeld()) multicastLock.release(); }
            catch (RuntimeException ignored) {}
            multicastLock=null;
        }
        if (registration != null) {
            try { nsd.unregisterService(registration); }
            catch (Exception ignored) {}
            registration = null;
        }
        requests.clear();
        show("Desligado. Não existe transferência de dados.");
    }

    private void acceptLoop() {
        while (running) {
            try {
                Socket peer = server.accept();
                new Thread(() -> respond(peer),"sp-core-lan-request").start();
            } catch (java.net.SocketTimeoutException ignored) {
            } catch (IOException ex) {
                if (running) show("Ligação interrompida: "+ex.getMessage());
                break;
            }
        }
    }

    private static String output(JSONObject data) {
        return data.toString();
    }
    private static JSONObject json(String key, Object value) {
        JSONObject object = new JSONObject();
        try { object.put(key,value); }
        catch (Exception ignored) {}
        return object;
    }

    private void respond(Socket peer) {
        try (Socket socket = peer) {
            socket.setSoTimeout(3500);
            BufferedReader reader = new BufferedReader(new InputStreamReader(
                socket.getInputStream(),StandardCharsets.UTF_8));
            BufferedWriter writer = new BufferedWriter(new OutputStreamWriter(
                socket.getOutputStream(),StandardCharsets.UTF_8));
            String first = reader.readLine();
            if (first == null || first.length() > 180) return;
            String[] request = first.split(" ");
            if (request.length != 3) return;
            int size = 0;
            String header;
            int seen = 0;
            while ((header = reader.readLine()) != null && !header.isEmpty()) {
                if (++seen > 30 || header.length() > 350) return;
                if (header.toLowerCase(java.util.Locale.ROOT).startsWith("content-length:")) {
                    size = Integer.parseInt(header.substring(header.indexOf(':')+1).trim());
                }
            }
            if (size < 0 || size > MAX_REQUEST) return;
            char[] body = new char[size];
            int done = 0;
            while (done < size) {
                int received = reader.read(body,done,size-done);
                if (received <= 0) return;
                done += received;
            }
            String method=request[0],path=request[1];
            JSONObject result;
            int statusCode = 200;
            if (method.equals("GET") && path.equals("/v1/status")) {
                result = json("protocol", PROTO);
                result.put("mode","link-only");
                result.put("device","SaúdePrática Android · Ligação Windows");
                result.put("ready",running);
            } else if (method.equals("POST") && path.equals("/v1/request")) {
                JSONObject input = new JSONObject(new String(body));
                String code = input.optString("code","");
                String nonce = input.optString("nonce","");
                if (!PROTO.equals(input.optString("protocol"))
                    || !code.matches("[0-9]{6}") || !nonce.matches("[a-fA-F0-9]{32}")) {
                    statusCode=400;
                    result=json("error","Pedido inválido.");
                } else if (requests.size()>8) {
                    statusCode=429;
                    result=json("error","Demasiados pedidos.");
                } else {
                    final String id=UUID.randomUUID().toString();
                    Pending pending=new Pending(code);
                    requests.put(id,pending);
                    statusCode=202;
                    result=json("request_id",id);
                    runOnUiThread(() -> {
                        if (!running) { pending.state="rejected"; return; }
                        new AlertDialog.Builder(this)
                            .setTitle("Pedido de ligação do Windows")
                            .setMessage("Código que deve aparecer IGUAL no Windows:\n\n"
                                + code + "\n\nAutorizar apenas o TESTE de ligação?\n"
                                + "Nenhum registo, fotografia ou documento será enviado.")
                            .setPositiveButton("Autorizar", (d,w) -> {
                                pending.state="accepted";
                                show("Ligação de teste AUTORIZADA · Código "+code+
                                    "\nSem sincronização de dados.");
                            })
                            .setNegativeButton("Recusar", (d,w) -> {
                                pending.state="rejected";
                                show("Ligação recusada.");
                            })
                            .setOnCancelListener(d -> { pending.state="rejected"; })
                            .show();
                    });
                }
            } else if (method.equals("GET") && path.startsWith("/v1/result?id=")) {
                String id=path.substring("/v1/result?id=".length());
                Pending pending=requests.get(id);
                if (pending==null) {
                    statusCode=404;
                    result=json("error","Pedido desconhecido.");
                } else {
                    if (System.currentTimeMillis()-pending.created>120000 &&
                            pending.state.equals("pending")) pending.state="expired";
                    result=json("state",pending.state);
                }
            } else {
                statusCode=404;
                result=json("error","Serviço indisponível.");
            }
            byte[] payload=output(result).getBytes(StandardCharsets.UTF_8);
            String head="HTTP/1.1 "+statusCode+" "+
                    (statusCode==200?"OK":statusCode==202?"Accepted":"Error")+"\r\n"
                +"Content-Type: application/json; charset=utf-8\r\n"
                +"Content-Length: "+payload.length+"\r\n"
                +"Connection: close\r\nCache-Control: no-store\r\n\r\n";
            socket.getOutputStream().write(head.getBytes(StandardCharsets.UTF_8));
            socket.getOutputStream().write(payload);
            socket.getOutputStream().flush();
        } catch (Exception ignored) {
            // Malformed requests never affect the existing SaúdePrática application.
        }
    }

    @Override protected void onDestroy() {
        stop();
        super.onDestroy();
    }
}
