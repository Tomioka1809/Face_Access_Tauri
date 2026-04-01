import { useState, useEffect, useRef, useCallback } from "react";
import "./App.css";

function App() {
  const [status, setStatus] = useState("Esperando Acción");
  const [mode, setMode] = useState("idle"); // 'idle', 'login', 'signup'
  const [bbox, setBbox] = useState(null);
  const [mesh, setMesh] = useState(null);
  const [signupName, setSignupName] = useState("");
  const [signupPassword, setSignupPassword] = useState("");
  const [cameraReady, setCameraReady] = useState(false);
  const [meshColor, setMeshColor] = useState("#3b82f6");

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const wsRef = useRef(null);
  const isFrozenRef = useRef(false);
  const modeRef = useRef(mode);
  const timeoutRef = useRef(null);

  useEffect(() => { modeRef.current = mode; }, [mode]);

  // Iniciar la Cámara Web Local HTML5
  useEffect(() => {
    let isMounted = true; // Bandera para saber si React destruyó este ciclo
    let currentStream = null;

    const startCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 1280, height: 720, facingMode: "user" }
        });

        // ¡EL TRUCO MÁGICO! 
        // Si React desmontó este componente mientras la cámara se encendía, la apagamos y salimos.
        if (!isMounted) {
          stream.getTracks().forEach(track => track.stop());
          return;
        }

        currentStream = stream;
        const video = videoRef.current;
        if (!video) return;

        video.srcObject = stream;

        // Esperar a que el video tenga sus metadatos listos para reproducir
        video.onloadedmetadata = () => {
          video.play()
            .then(() => setCameraReady(true))
            .catch((e) => console.error("Error al reproducir video:", e));
        };

      } catch (err) {
        console.error("Error al acceder a la cámara:", err);
        setStatus("Error: Sin permisos de cámara");
      }
    };

    startCamera();

    return () => {
      isMounted = false; // Avisamos que este ciclo murió
      // Limpiar el stream de la cámara al desmontar
      if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
      }
    };
  }, []);

  // Iniciar conexión permanente WebSocket a Python (Localhost a diferencia de Web pura)
  useEffect(() => {
    // Apuntamos al Sidecar de Python en su puerto local por defecto de FastAPI
    const ws = new WebSocket("ws://127.0.0.1:8000/ws/stream");

    ws.onopen = () => {
      console.log("✅ WebSocket Conectado a Python FastAPI");
      setStatus("Conexión Python Establecida");
    };

    ws.onmessage = (event) => {
      if (isFrozenRef.current) return; // Si estamos en pantalla de éxito/error, no sobrescribir mensajes

      const response = JSON.parse(event.data);
      if (response.status) setStatus(response.status);
      if (response.bbox) setBbox(response.bbox); // [xi, yi, xf, yf]
      else setBbox(null);
      if (response.mesh) setMesh(response.mesh); // Malla facial (Face Mesh)
      else setMesh(null);

      // Manejar el resultado definitivo (éxito o fallo)
      if (response.result === "success" || response.result === "failed") {
        isFrozenRef.current = true;

        if (response.result === "success") {
          setMeshColor("#10b981"); // Verde esmeralda (éxito)
        } else {
          setMeshColor("#ef4444"); // Rojo (fallo)
        }

        const currentMode = modeRef.current;
        const waitTime = currentMode === "signup" ? 10000 : 5000;

        if (timeoutRef.current) clearTimeout(timeoutRef.current);
        timeoutRef.current = setTimeout(() => {
          isFrozenRef.current = false;
          setMeshColor("#3b82f6"); // Volver a azul
          
          if (response.result === "success") {
            setMode("idle");
            setStatus("Esperando Acción");
            setSignupName("");
            setSignupPassword("");
          } else {
            // Si falló, mantén el modo y actualiza el estado para reintentar
            setStatus(currentMode === "signup" ? "Mire a la cámara para reintentar registro..." : "Reintentando leer rostro...");
          }
        }, waitTime);
      }
    };

    ws.onclose = () => {
      console.log("❌ WebSocket Desconectado");
      setStatus("Python Sidecar Apagado");
    };

    wsRef.current = ws;

    return () => {
      if (ws.readyState === 1) ws.close();
    };
  }, []);

  // Bucle de Streaming: Enviar Fotogramas de React a Python (Milisegundos)
  const sendFrameToPython = useCallback(() => {
    if (!videoRef.current || !canvasRef.current || !wsRef.current) return;
    if (wsRef.current.readyState !== WebSocket.OPEN) return;
    if (mode === "idle" || isFrozenRef.current) return; // Ahorrar CPU si no estan haciendo nada o pantalla congelada

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas.getContext("2d");

    // Copiamos la imagen del video al canvas
    canvas.width = video.videoWidth || 1280;
    canvas.height = video.videoHeight || 720;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convertimos a base64 MUY LIGERO (calidad 60%) para el WebSocket
    const imageData = canvas.toDataURL("image/jpeg", 0.6);

    // Mandamos el Dict JSON
    wsRef.current.send(JSON.stringify({
      mode: mode,
      image: imageData,
      username: signupName,
      password: signupPassword
    }));
  }, [mode, signupName, signupPassword]);

  // Ejecutar el Streaming a 15-20 FPS mediante setInterval
  useEffect(() => {
    const interval = setInterval(sendFrameToPython, 60); // ~16 FPS
    return () => clearInterval(interval);
  }, [sendFrameToPython]);

  return (
    <div className="min-h-screen bg-dark w-full flex flex-col items-center justify-center p-6 text-white font-sans selection:bg-primary selection:text-white">

      {/* Controles Ocultos para Cálculos */}
      <canvas ref={canvasRef} style={{ display: "none" }} />

      <div className="bg-surface/80 backdrop-blur-md border border-white/10 rounded-3xl shadow-2xl p-8 max-w-4xl w-full grid grid-cols-1 md:grid-cols-2 gap-8">

        {/* Panel Izquierdo: Cámara */}
        <div className="flex flex-col items-center gap-4">
          <div className="w-full aspect-video bg-black/80 border border-white/5 rounded-2xl flex relative overflow-hidden group">
            <span className="text-white/30 text-xs font-medium tracking-widest absolute top-2 left-3 z-10">TAURI PREVIEW</span>

            {/* Spinner mientras la cámara no está lista */}
            {!cameraReady && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/60 z-10">
                <div className="flex flex-col items-center gap-3">
                  <div className="w-10 h-10 rounded-full border-4 border-primary border-t-transparent animate-spin"></div>
                  <span className="text-white/50 text-xs tracking-widest">INICIANDO CÁMARA...</span>
                </div>
              </div>
            )}

            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              className="w-full h-full object-cover z-0"
              style={mode !== "idle" ? {} : { filter: "grayscale(70%) blur(1px)" }}
            />

            {/* Dibujar la malla virtual (Face Mesh) calculada desde Python */}
            {mesh && mode !== "idle" && (
              <svg className="absolute inset-0 w-full h-full pointer-events-none z-10" viewBox="0 0 1280 720">
                {mesh.map((pt, i) => (
                  <circle key={`pt-${i}`} cx={pt[1]} cy={pt[2]} r={2.5} fill={meshColor} opacity={0.65} />
                ))}
              </svg>
            )}

            {/* Eliminada la caja cuadrada (bbox) por petición del usuario */}
          </div>

          <p className="text-sm text-gray-400 font-medium px-4 py-2 bg-black/40 rounded-full flex gap-2 items-center">
            Estado de IA:
            <span className={`font-bold transition-colors ${mode === "idle" ? "text-gray-500" : "text-primary"}`}>
              {status}
            </span>
          </p>
        </div>

        {/* Panel Derecho: Controles */}
        <div className="flex flex-col justify-center gap-6">
          <div className="mb-4">
            <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-primary">
              Access Control
            </h1>
            <p className="text-gray-400 text-sm mt-2">
              Biometría Facial con MediaPipe + Tauri
            </p>
          </div>

          <div className="flex flex-col gap-4">
            {mode === "idle" && (
              <>
                <button
                  className="w-full py-3 px-6 rounded-xl font-bold tracking-wide transition-all duration-300 relative overflow-hidden group border border-primary/50 bg-primary/10 hover:bg-primary hover:shadow-[0_0_20px_rgba(59,130,246,0.3)]"
                  onClick={() => setMode("login")}
                >
                  <span className="relative z-10">INICIAR SESIÓN</span>
                </button>

                <button
                  className="w-full py-3 px-6 rounded-xl font-bold tracking-wide transition-all duration-300 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20"
                  onClick={() => setMode("signupForm")}
                >
                  REGISTRAR USUARIO
                </button>
              </>
            )}

            {mode === "signupForm" && (
              <form
                className="flex flex-col gap-4 bg-black/20 p-5 rounded-2xl border border-white/10"
                onSubmit={(e) => {
                  e.preventDefault();
                  if (signupName.trim() !== "" && signupPassword.trim() !== "") {
                    setMode("signup");
                    setStatus("Mire a la cámara para registrar su rostro...");
                  }
                }}
              >
                <div className="flex flex-col gap-2">
                  <label className="text-xs text-gray-400 uppercase tracking-widest font-bold">Usuario</label>
                  <input
                    type="text"
                    required
                    value={signupName}
                    onChange={(e) => setSignupName(e.target.value)}
                    className="bg-black/40 border border-white/5 rounded-xl px-4 py-3 text-white outline-none focus:border-primary focus:bg-white/5 transition-colors"
                  />
                </div>
                <div className="flex flex-col gap-2">
                  <label className="text-xs text-gray-400 uppercase tracking-widest font-bold">Contraseña</label>
                  <input
                    type="password"
                    required
                    value={signupPassword}
                    onChange={(e) => setSignupPassword(e.target.value)}
                    className="bg-black/40 border border-white/5 rounded-xl px-4 py-3 text-white outline-none focus:border-primary focus:bg-white/5 transition-colors"
                  />
                </div>
                <div className="flex gap-3 mt-2">
                  <button type="submit" className="flex-1 bg-primary text-white py-3 rounded-xl font-bold hover:bg-blue-600 transition-colors shadow-lg shadow-primary/20">
                    Siguiente
                  </button>
                  <button type="button" onClick={() => {
                    setMode("idle");
                    setSignupName("");
                    setSignupPassword("");
                  }} className="flex-1 bg-white/5 text-white py-3 rounded-xl hover:bg-white/10 transition-colors">
                    Cancelar
                  </button>
                </div>
              </form>
            )}

            {(mode === "login" || mode === "signup") && (
              <button
                className="w-full py-3 px-6 rounded-xl font-bold tracking-wide transition-all duration-300 bg-red-500/20 text-red-400 border border-red-500/50 hover:bg-red-500 hover:text-white"
                onClick={() => {
                  if (timeoutRef.current) clearTimeout(timeoutRef.current);
                  isFrozenRef.current = false;
                  setMeshColor("#3b82f6");
                  setMode("idle");
                  setStatus("Cancelado por Usuario");
                  setSignupName("");
                  setSignupPassword("");
                }}
              >
                CANCELAR {mode === "signup" ? "REGISTRO" : "LOGIN"}
              </button>
            )}
          </div>

          <div className="mt-8 pt-6 border-t border-white/10 flex justify-between text-xs text-gray-500 font-mono">
            <span>FastAPI: localhost:8000</span>
            <span>Tauri + React</span>
          </div>
        </div>

      </div>
    </div>
  );
}

export default App;
