package com.mediagenda.app;

import android.app.DownloadManager;
import android.content.Context;
import android.content.SharedPreferences;
import android.os.Environment;
import java.io.File;
import java.security.KeyStore;

/**
 * One-time, narrowly scoped cleanup of the OPTIONAL assistant downloaded by
 * Android versions 1.9.130–1.9.132. Never touches any clinical or backup files.
 *
 * The on-device Qwen model lived in filesDir/ia-local, outside the Android app
 * package. Removing the runtime without removing the file would waste ~383 MB.
 *
 * Also cancels the assistant's DownloadManager job and removes ONLY the optional
 * online assistant's own endpoint/secret and keystore alias. The Gemini key used
 * by meal recognition and unrelated modules is intentionally NOT touched.
 */
public final class LegacyAssistantCleanup {
    private static final String MODEL = "Qwen3-0.6B-Q4_K_S.gguf";
    private static final String MARKER = "saudepratica_ai_removal_v133";
    private static final String KEY_ALIAS = "saudepratica_online_ai_token_v1";

    private LegacyAssistantCleanup() {}

    public static void run(Context context) {
        final Context app = context.getApplicationContext();
        final SharedPreferences marker = app.getSharedPreferences(MARKER, Context.MODE_PRIVATE);
        if (marker.getBoolean("completed", false)) return;

        Thread cleaner = new Thread(() -> {
            boolean removed = true;
            try {
                SharedPreferences downloads =
                    app.getSharedPreferences("saudepratica_ia_model_download", Context.MODE_PRIVATE);
                long id = downloads.getLong("download_id", -1L);
                if (id >= 0) {
                    try {
                        DownloadManager manager =
                            (DownloadManager) app.getSystemService(Context.DOWNLOAD_SERVICE);
                        if (manager != null) manager.remove(id);
                    } catch (Exception ignored) {
                        // Job may have completed, been removed or lost its ID.
                    }
                }
                downloads.edit().remove("download_id").commit();

                File folder = new File(app.getFilesDir(), "ia-local");
                for (String name : new String[] {
                        MODEL, MODEL + ".part", MODEL + ".install" }) {
                    File file = new File(folder, name);
                    if (file.exists() && !file.delete()) removed = false;
                }
                // Only remove the directory when it is empty. Never touch
                // unexpected files that may have been placed there.
                if (folder.isDirectory()) folder.delete();

                File external = app.getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS);
                if (external != null) {
                    File pending = new File(external, MODEL);
                    if (pending.exists() && !pending.delete()) removed = false;
                }

                app.getSharedPreferences("saudepratica_online_ai", Context.MODE_PRIVATE)
                    .edit().remove("endpoint").remove("credential").commit();
                app.getSharedPreferences("mediagenda_ui", Context.MODE_PRIVATE)
                    .edit().remove("saude_online_ai_mode").commit();

                try {
                    KeyStore ks = KeyStore.getInstance("AndroidKeyStore");
                    ks.load(null);
                    if (ks.containsAlias(KEY_ALIAS)) ks.deleteEntry(KEY_ALIAS);
                } catch (Exception ignored) {
                    // If Keystore is locked, the encrypted token is already
                    // unusable without the removed encrypted preferences.
                }
            } catch (Exception ignored) {
                removed = false;
            }

            // Retry next app launch on failed model-file removal.
            if (removed) marker.edit().putBoolean("completed", true).commit();
        }, "SaudePratica-Remover-Modelo-IA-Antigo");
        cleaner.setDaemon(true);
        cleaner.start();
    }
}
