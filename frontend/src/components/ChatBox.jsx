import { useState, useRef, useEffect } from "react";
import { Mic, MicOff, Volume2, VolumeX } from "lucide-react";
import { sendChatMessage } from "../api";
import { useLanguage } from "../i18n/LanguageContext";

export default function ChatBox({ soil, selectedCrop }) {
  const { t, lang } = useLanguage();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [speakingIndex, setSpeakingIndex] = useState(null);
  const [isListening, setIsListening] = useState(false);
  const scrollRef = useRef(null);
  const recognitionRef = useRef(null);

  const hasRecognition = typeof window !== "undefined" && Boolean(window.SpeechRecognition || window.webkitSpeechRecognition);
  const hasSynthesis = typeof window !== "undefined" && Boolean("speechSynthesis" in window);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try { recognitionRef.current.abort(); } catch (_) {}
      }
      if (hasSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, [hasSynthesis]);

  function toggleSpeech() {
    if (!hasRecognition) return;
    if (isListening) {
      recognitionRef.current?.abort();
      setIsListening(false);
      return;
    }
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = lang === "hi" ? "hi-IN" : lang === "mr" ? "mr-IN" : "en-IN";
    recognition.onstart = () => setIsListening(true);
    recognition.onresult = (e) => {
      const transcript = e.results[0][0].transcript;
      if (transcript) setInput(transcript);
    };
    recognition.onerror = () => setIsListening(false);
    recognition.onend = () => setIsListening(false);
    recognitionRef.current = recognition;
    recognition.start();
  }

  function speakText(text, index) {
    if (!hasSynthesis) return;
    if (speakingIndex === index) {
      window.speechSynthesis.cancel();
      setSpeakingIndex(null);
      return;
    }
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang === "hi" ? "hi-IN" : lang === "mr" ? "mr-IN" : "en-IN";
    utterance.rate = 0.92;
    utterance.onend = () => setSpeakingIndex(null);
    utterance.onerror = () => setSpeakingIndex(null);
    window.speechSynthesis.speak(utterance);
    setSpeakingIndex(index);
  }

  async function handleSend() {
    const text = input.trim();
    if (!text || sending) return;
    setMessages((m) => [...m, { role: "user", text }]);
    setInput("");
    setSending(true);
    try {
      const res = await sendChatMessage(text, soil, selectedCrop, lang);
      setMessages((m) => [...m, { role: "assistant", text: res.answer, contradiction: res.contradiction_flag }]);
    } catch (err) {
      setMessages((m) => [...m, { role: "assistant", text: `Sorry, something went wrong: ${err.message}` }]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="surface-card rounded-2xl border border-soil-300/70 flex flex-col h-96 overflow-hidden">
      <div className="px-5 py-4 border-b border-soil-200 bg-white/60 flex items-center justify-between">
        <h3 className="font-display text-lg font-semibold text-soil-900">{t("chatHeading")}</h3>
        <span className="text-xs font-mono text-soil-500 bg-soil-100 px-2 py-0.5 rounded">
          {lang === "hi" ? "hi-IN" : lang === "mr" ? "mr-IN" : "en-IN"}
        </span>
      </div>
      <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
        {messages.length === 0 && (
          <div className="flex justify-start">
            <div className="max-w-[85%] rounded-2xl rounded-tl-md px-4 py-3 text-sm bg-soil-100 text-soil-900">
              {t("chatGreeting")}
            </div>
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 text-sm shadow-sm space-y-1.5 ${
                m.role === "user" ? "rounded-tr-md bg-leaf-600 text-white" : "rounded-tl-md bg-soil-100 text-soil-900"
              }`}
            >
              <p>{m.text}</p>
              {m.role === "assistant" && (
                <div className="pt-1 flex items-center justify-end">
                  <button
                    type="button"
                    onClick={() => speakText(m.text, i)}
                    className="inline-flex items-center gap-1 text-[11px] text-forest-800 hover:text-forest-950 font-medium"
                    title={speakingIndex === i ? t("voiceStopSpeaking") : t("voiceReadAloud")}
                  >
                    {speakingIndex === i ? <VolumeX className="h-3 w-3 text-red-600" /> : <Volume2 className="h-3 w-3" />}
                    <span>{speakingIndex === i ? t("voiceStopSpeaking") : t("voiceReadAloud")}</span>
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
        {sending && (
          <div className="flex items-center gap-2 text-xs text-soil-500" role="status">
            <span className="flex items-center gap-1" aria-hidden="true">
              <i className="typing-dot h-1.5 w-1.5 rounded-full bg-leaf-500" />
              <i className="typing-dot h-1.5 w-1.5 rounded-full bg-leaf-500" />
              <i className="typing-dot h-1.5 w-1.5 rounded-full bg-leaf-500" />
            </span>
            {t("chatThinking")}
          </div>
        )}
      </div>
      <div className="p-3 border-t border-soil-200 flex gap-2 bg-white/60 items-center">
        {hasRecognition && (
          <button
            type="button"
            onClick={toggleSpeech}
            className={`p-2.5 rounded-xl transition-all ${
              isListening ? "bg-red-500 text-white animate-pulse" : "border border-soil-300 bg-white text-soil-700 hover:bg-soil-100"
            }`}
            title={isListening ? t("voiceCancelListening") : t("micStart")}
          >
            {isListening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
          </button>
        )}
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSend()}
          placeholder={isListening ? t("micListening") : t("chatInputPlaceholder")}
          className="flex-1 min-w-0 px-3 py-2.5 rounded-xl border border-soil-300/80 bg-white text-sm focus:outline-none focus:ring-2 focus:ring-leaf-500"
        />
        <button
          onClick={handleSend}
          disabled={sending || !input.trim()}
          className="px-4 py-2.5 rounded-xl bg-soil-900 hover:bg-soil-700 text-white text-sm font-medium disabled:opacity-50 transition-colors"
        >
          {t("chatSend")}
        </button>
      </div>
    </div>
  );
}
