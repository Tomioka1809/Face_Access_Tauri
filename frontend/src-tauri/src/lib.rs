use tauri::Manager;

// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![greet])
        .setup(|app| {
            let webview_window = app.get_webview_window("main").unwrap();

            #[cfg(target_os = "linux")]
            {
                use webkit2gtk::WebViewExt;
                use webkit2gtk::SettingsExt;
                use webkit2gtk::PermissionRequestExt;

                webview_window.with_webview(|webview| {
                    let wk = webview.inner();

                    // Habilitar acceso a medios (cámara/micrófono) en WebKit para Linux
                    if let Some(settings) = wk.settings() {
                        settings.set_enable_media_stream(true);
                        settings.set_enable_media_capabilities(true);
                        settings.set_media_playback_requires_user_gesture(false);
                        settings.set_enable_encrypted_media(true);
                    }

                    // Aprobar automáticamente cualquier solicitud de permiso (cámara, micrófono)
                    wk.connect_permission_request(|_view, request| {
                        request.allow();
                        true
                    });
                }).ok();
            }

            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
