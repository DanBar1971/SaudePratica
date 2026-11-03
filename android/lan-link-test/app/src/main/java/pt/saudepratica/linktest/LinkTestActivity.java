package pt.saudepratica.linktest;

import android.app.Activity;
import android.app.AlertDialog;
import android.os.Bundle;
import android.os.Build;
import android.net.nsd.NsdManager;
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
 * ISOLATED Android <-> Windows discovery / approval demonstration.
 *
 * Does NOT read clinical app storage or transmit private data. This temporary
 * proof-of-connection uses HTTP over local Wi-Fi with a six-digit displayed
 * code and manual consent. It is NOT secure enough for medical sync. A future
 * production protocol MUST authenticate and encrypt the data channel.
 */
public final class LinkTestActivity extends Activity {
    private static final String TYPE = "_saudepratica-sync._tcp.";
    private static final String PROTO = "sp-pair-test-0";
    private static final int MAX_REQUEST = 1024;
    private volatile boolean running = false;
    private ServerSocket server;
    private NsdManager nsd;
    private NsdManager.RegistrationListener registration;
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
        view.setTextColor(DARK);
        view.setBackgroundTintList(android.content.res.ColorStateList.valueOf(TEAL));
        view.setOnClickListener(v -> action.run());
        return view;
    }

    @Override public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        nsd = (NsdManager) getSystemService(NSD_SERVICE);
        ScrollView scroller = new ScrollView(this);
        scroller.setBackgroundColor(DARK);
        LinearLayout body = new LinearLayout(this);
        body.setOrientation(LinearLayout.VERTICAL);
        body.setPadding(24, 26, 24, 26);
        scroller.addView(body);
        body.addView(text("SaúdePrática\nLigação Wi-Fi · TESTE", 26, true));
        body.addView(text("Aplicação auxiliar para experimentar a descoberta automática "
                + "pelo Windows e confirmar o pedido no Android. "
                + "A aplicação SaúdePrática original permanece instalada e inalterada.", 15, false));
        body.addView(text("NÃO sincroniza dados médicos, perfis, medicação, agenda ou fotografias.", 16, true));
        body.addView(button("1 · Tornar visível na rede local", this::start));
        body.addView(button("2 · Parar / desligar", this::stop));
        status = text("Desligado. Liga o Wi-Fi e toca em «Tornar visível».", 16, true);
        body.addView(status);
        detail = text("No Windows, abre SaúdePrática → Mais módulos → Sincronização. "
                + "O PC deve descobrir este telemóvel automaticamente. "
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

    private synchronized void start() {
        if (running) { show("Já está visível. Espera o pedido do Windows."); return; }
        try {
            server = new ServerSocket(0);
            server.setSoTimeout(1300);
            running = true;
            final int port = server.getLocalPort();
            show("A iniciar descoberta...");
            new Thread(this::acceptLoop, "sp-link-test-server").start();
            NsdServiceInfo info = new NsdServiceInfo();
            info.setServiceName("SaudePratica Ligacao " + Build.MODEL.replaceAll("[^a-zA-Z0-9 _-]", "").trim());
            info.setServiceType(TYPE);
            info.setPort(port);
            info.setAttribute("proto", PROTO);
            info.setAttribute("mode", "link-only");
            info.setAttribute("name", ("SaúdePrática Teste · " + Build.MODEL).substring(
                0, Math.min(60, ("SaúdePrática Teste · " + Build.MODEL).length())));
            registration = new NsdManager.RegistrationListener() {
                @Override public void onServiceRegistered(NsdServiceInfo registered) {
                    show("VISÍVEL · "+registered.getServiceName()+
                         "\nIP: "+localAddress()+"   Porta: "+port+
                         "\nAguardando pedido do Windows...");
                }
                @Override public void onRegistrationFailed(NsdServiceInfo entry, int code) {
                    show("Descoberta automática falhou ("+code+").\n"
                        +"Podes tentar por IP: "+localAddress()+" · Porta "+port);
                }
                @Override public void onServiceUnregistered(NsdServiceInfo entry) {
                    show("Desligado.");
                }
                @Override public void onUnregistrationFailed(NsdServiceInfo entry, int code) {
                    show("Erro ao desligar a descoberta: "+code);
                }
            };
            nsd.registerService(info,NsdManager.PROTOCOL_DNS_SD,registration);
        } catch (Exception e) {
            running = false;
            if (server != null) try { server.close(); } catch (IOException ignored) {}
            show("Não foi possível abrir a ligação: "+e.getMessage());
        }
    }

    private synchronized void stop() {
        running = false;
        if (server != null) try { server.close(); } catch (IOException ignored) {}
        server = null;
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
                new Thread(() -> respond(peer),"sp-link-test-request").start();
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
                result.put("device","SaúdePrática Android · Teste");
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
