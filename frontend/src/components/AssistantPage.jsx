import { useState, useRef, useEffect, useCallback } from "react";
import {
  Send,
  Bot,
  User,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  AlertCircle,
  ShieldAlert,
  Info,
  CheckCircle2,
  RefreshCw,
  X,
  FileText,
  Sparkles,
} from "lucide-react";
import { sendChatMessage } from "../api";
import { useLanguage } from "../i18n/LanguageContext";

export default function AssistantPage({ soil, selectedCrop, location, applicationWindow }) {
  const { t, lang, setLang } = useLanguage();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);

  // Voice Speech-to-Text State
  // "idle" | "listening" | "processing" | "error"
  const [speechState, setSpeechState] = useState("idle");
  const [speechError, setSpeechError] = useState(null);
  const [transcriptReady, setTranscriptReady] = useState(false);

  // Voice Text-to-Speech State
  const [speakingIndex, setSpeakingIndex] = useState(null);
  const [voiceNotice, setVoiceNotice] = useState(null);
  const [availableVoices, setAvailableVoices] = useState([]);

  const scrollRef = useRef(null);
  const inputRef = useRef(null);
  const recognitionRef = useRef(null);

  // Check Web Speech API capability
  const hasRecognition = typeof window !== "undefined" && Boolean(window.SpeechRecognition || window.webkitSpeechRecognition);
  const hasSynthesis = typeof window !== "undefined" && Boolean("speechSynthesis" in window);

  // Load available system voices
  useEffect(() => {
    if (!hasSynthesis) return;

    function updateVoices() {
      const voices = window.speechSynthesis.getVoices();
      setAvailableVoices(voices || []);
    }

    updateVoices();
    window.speechSynthesis.onvoiceschanged = updateVoices;

    return () => {
      window.speechSynthesis.cancel();
    };
  }, [hasSynthesis]);

  // Cleanup recognition on unmount
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch (_) {}
      }
      if (hasSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, [hasSynthesis]);

  // Auto-scroll on messages or status update
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, sending, speechState]);

  // Suggested prompt chips
  const weatherSuggestion =
    lang === "mr"
      ? "मुंबईचे सध्याचे तापमान काय आहे?"
      : lang === "hi"
      ? "मुंबई में अभी तापमान क्या है?"
      : "What's the temperature in Mumbai now?";

  const suggestions = [
    weatherSuggestion,
    t("suggestedQ1"),
    t("suggestedQ2"),
    t("suggestedQ3"),
  ];

  // Map language code to speech locale
  const speechLocale = lang === "hi" ? "hi-IN" : lang === "mr" ? "mr-IN" : "en-IN";
  const languageDisplayName = lang === "hi" ? "हिंदी (hi-IN)" : lang === "mr" ? "मराठी (mr-IN)" : "English (en-IN)";

  // Send message to AgriMind backend
  async function handleSend(textToSend) {
    const text = (textToSend || input).trim();
    if (!text || sending) return;

    // Stop listening or speaking if active
    cancelListening();
    stopSpeaking();

    setMessages((prev) => [...prev, { role: "user", text }]);
    setInput("");
    setTranscriptReady(false);
    setSending(true);
    setSpeechError(null);

    try {
      const res = await sendChatMessage(text, soil, selectedCrop, lang, location, applicationWindow);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: res.answer,
          contradiction: res.contradiction_flag,
          evidence: res.evidence,
          llmProvider: res.llm_provider,
          llmModel: res.llm_model,
          isFallback: res.is_llm_fallback,
          language: res.language || lang,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: `We could not reach the server: ${err.message}. If the backend is offline, please ensure uvicorn is running.`,
          isFallback: true,
          llmProvider: "error",
        },
      ]);
    } finally {
      setSending(false);
    }
  }

  // Web Speech API: Start Speech-to-Text
  function startListening() {
    if (!hasRecognition) {
      setSpeechError(t("voiceNotSupported"));
      return;
    }

    // Stop speaking if active
    stopSpeaking();

    // Abort any existing instance
    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch (_) {}
    }

    try {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.maxAlternatives = 1;
      recognition.lang = speechLocale;

      recognition.onstart = () => {
        setSpeechState("listening");
        setSpeechError(null);
        setTranscriptReady(false);
      };

      recognition.onspeechstart = () => {
        setSpeechState("listening");
      };

      recognition.onspeechend = () => {
        setSpeechState("processing");
      };

      recognition.onresult = (event) => {
        let interimTranscript = "";
        let finalTranscript = "";

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const piece = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += piece;
          } else {
            interimTranscript += piece;
          }
        }

        const candidate = finalTranscript || interimTranscript;
        if (candidate) {
          setInput(candidate);
          if (finalTranscript) {
            setTranscriptReady(true);
            setSpeechState("idle");
          }
        }
      };

      recognition.onerror = (event) => {
        setSpeechState("error");
        const code = event.error;

        if (code === "not-allowed" || code === "permission-denied") {
          setSpeechError(t("voiceMicBlocked"));
        } else if (code === "no-speech") {
          setSpeechError(t("voiceNoSpeech"));
        } else if (code === "network") {
          setSpeechError(t("voiceNetworkError"));
        } else if (code === "language-not-supported") {
          setSpeechError(t("voiceLangUnsupported"));
        } else if (code === "aborted") {
          setSpeechState("idle");
        } else {
          setSpeechError(`Voice input issue (${code}). You can type your question in the text box.`);
        }
      };

      recognition.onend = () => {
        // Guarantee mic indicator never keeps running after recognition finishes
        setSpeechState((prev) => (prev === "listening" || prev === "processing" ? "idle" : prev));
        recognitionRef.current = null;
        if (inputRef.current) {
          inputRef.current.focus();
        }
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      setSpeechState("error");
      setSpeechError(`Microphone initialization failed: ${err.message}`);
      recognitionRef.current = null;
    }
  }

  // Cancel or Stop Speech-to-Text
  function cancelListening() {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch (_) {}
      recognitionRef.current = null;
    }
    setSpeechState("idle");
  }

  // Web Speech API: Text-to-Speech
  const speakText = useCallback(
    (text, index) => {
      if (!hasSynthesis) return;

      // If already speaking this message, toggle off
      if (speakingIndex === index) {
        stopSpeaking();
        return;
      }

      window.speechSynthesis.cancel();
      setVoiceNotice(null);

      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.92; // Slightly measured rate for clear comprehension
      utterance.pitch = 1.0;

      // Find the best matching voice on the user's platform
      const targetPrefix = lang === "hi" ? "hi" : lang === "mr" ? "mr" : "en";
      const voices = window.speechSynthesis.getVoices();

      let matchedVoice = voices.find((v) => v.lang && v.lang.toLowerCase().replace("_", "-") === speechLocale.toLowerCase());
      if (!matchedVoice) {
        matchedVoice = voices.find((v) => v.lang && v.lang.toLowerCase().startsWith(targetPrefix));
      }

      // If Marathi native voice is not installed on device (common in desktop browsers):
      if (!matchedVoice && lang === "mr") {
        // Fallback to Hindi or Indian English voice
        matchedVoice =
          voices.find((v) => v.lang && v.lang.toLowerCase().startsWith("hi")) ||
          voices.find((v) => v.lang && v.lang.toLowerCase().includes("in")) ||
          null;
        setVoiceNotice(t("voiceFallbackVoiceNote"));
      }

      if (matchedVoice) {
        utterance.voice = matchedVoice;
        utterance.lang = matchedVoice.lang;
      } else {
        utterance.lang = speechLocale;
      }

      utterance.onstart = () => {
        setSpeakingIndex(index);
      };

      utterance.onend = () => {
        setSpeakingIndex(null);
      };

      utterance.onerror = () => {
        setSpeakingIndex(null);
      };

      window.speechSynthesis.speak(utterance);
    },
    [hasSynthesis, lang, speechLocale, speakingIndex, t]
  );

  function stopSpeaking() {
    if (hasSynthesis) {
      window.speechSynthesis.cancel();
    }
    setSpeakingIndex(null);
    setVoiceNotice(null);
  }

  return (
    <div className="max-w-4xl mx-auto space-y-5 py-6 sm:py-8">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-display text-2xl sm:text-3xl font-semibold text-forest-900 dark:text-white flex items-center gap-2.5">
            <Bot className="h-6 w-6 text-forest-800 dark:text-[#DAF1DE]" aria-hidden="true" />
            <span>{t("chatHeading")}</span>
          </h1>
          <p className="mt-1 text-sm text-soil-600 dark:text-white/90">{t("chatSub")}</p>
        </div>

        {/* Global Stop Audio Button (appears when assistant is speaking) */}
        {speakingIndex !== null && (
          <button
            type="button"
            onClick={stopSpeaking}
            className="inline-flex items-center gap-1.5 rounded-full border border-red-300 dark:border-red-800 bg-red-50 dark:bg-red-950/70 px-3.5 py-1.5 text-xs font-semibold text-red-800 dark:text-red-200 hover:bg-red-100 dark:hover:bg-red-900 transition-colors shadow-xs animate-pulse"
          >
            <VolumeX className="h-3.5 w-3.5" />
            <span>{t("voiceStopSpeaking")}</span>
          </button>
        )}
      </div>

      {/* Voice & Language Selection Bar */}
      <div className="rounded-2xl border border-soil-200 dark:border-[#235347] bg-white dark:bg-[#163832] p-3.5 shadow-xs flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-xs font-medium text-soil-700 dark:text-white">
          <span className="font-semibold text-forest-900 dark:text-white">{t("voiceLangSelectorLabel")}:</span>
          <div className="inline-flex rounded-lg border border-soil-200 dark:border-[#235347] bg-soil-50 dark:bg-[#0B2B26] p-0.5">
            <button
              type="button"
              onClick={() => setLang("en")}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-all ${
                lang === "en"
                  ? "bg-forest-900 dark:bg-[#235347] text-white shadow-xs"
                  : "text-soil-600 dark:text-[#FFFFFF] hover:text-forest-900 dark:hover:text-[#DAF1DE]"
              }`}
            >
              English
            </button>
            <button
              type="button"
              onClick={() => setLang("hi")}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-all ${
                lang === "hi"
                  ? "bg-forest-900 dark:bg-[#235347] text-white shadow-xs"
                  : "text-soil-600 dark:text-[#FFFFFF] hover:text-forest-900 dark:hover:text-[#DAF1DE]"
              }`}
            >
              हिंदी
            </button>
            <button
              type="button"
              onClick={() => setLang("mr")}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-all ${
                lang === "mr"
                  ? "bg-forest-900 dark:bg-[#235347] text-white shadow-xs"
                  : "text-soil-600 dark:text-[#FFFFFF] hover:text-forest-900 dark:hover:text-[#DAF1DE]"
              }`}
            >
              मराठी
            </button>
          </div>
          <span className="text-[11px] font-mono text-forest-800 dark:text-[#DAF1DE] bg-forest-50 dark:bg-[#0B2B26] px-2 py-0.5 rounded border border-forest-200 dark:border-[#235347]">
            {speechLocale}
          </span>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <span className="flex h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span className="font-semibold text-forest-900 dark:text-white">Active Farm:</span>
          <span className="font-mono text-xs text-forest-800 dark:text-[#DAF1DE] bg-soil-50 dark:bg-[#0B2B26] px-2.5 py-1 rounded-lg border border-soil-200 dark:border-[#235347]">
            {location || "Maharashtra"}
          </span>
        </div>
      </div>

      {/* Voice Warning / Fallback Notice */}
      {voiceNotice && (
        <div
          role="status"
          className="rounded-xl border border-sky-200 dark:border-sky-800 bg-sky-50 dark:bg-sky-950/60 p-3 text-xs text-sky-800 dark:text-sky-200 flex items-center justify-between gap-2"
        >
          <div className="flex items-center gap-2">
            <Info className="h-4 w-4 text-sky-600 dark:text-sky-400 shrink-0" />
            <span>{voiceNotice}</span>
          </div>
          <button
            type="button"
            onClick={() => setVoiceNotice(null)}
            className="text-sky-600 dark:text-sky-400 hover:text-sky-900 p-0.5"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}

      {/* Speech Error Banner */}
      {speechError && (
        <div
          role="alert"
          className="rounded-xl border border-amber-300 dark:border-amber-800 bg-amber-50 dark:bg-amber-950/60 p-3 text-xs text-amber-900 dark:text-amber-200 flex items-center justify-between gap-2"
        >
          <div className="flex items-center gap-2">
            <AlertCircle className="h-4 w-4 text-amber-700 dark:text-amber-400 shrink-0" />
            <span>{speechError}</span>
          </div>
          <button
            type="button"
            onClick={() => setSpeechError(null)}
            className="text-amber-700 dark:text-amber-400 hover:text-amber-950 p-0.5"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}

      {/* Chat Area Container */}
      <div className="rounded-2xl border border-soil-200 dark:border-[#235347] bg-white dark:bg-[#163832] overflow-hidden shadow-soft flex flex-col h-[580px]">
        {/* Messages Scroll Area */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
          {/* Greeting message */}
          <div className="flex items-start gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-forest-900 dark:bg-[#235347] text-white shrink-0 mt-0.5">
              <Bot className="h-4 w-4" />
            </div>
            <div className="rounded-2xl rounded-tl-sm bg-soil-50 dark:bg-[#0B2B26] border border-soil-200 dark:border-[#235347] px-4 py-3 text-sm text-forest-900 dark:text-[#FFFFFF] max-w-[85%] space-y-2">
              <p className="leading-relaxed font-normal">{t("chatGreeting")}</p>
              {soil && (
                <div className="text-[11px] font-mono text-forest-800 dark:text-[#DAF1DE] bg-forest-50 dark:bg-[#163832] rounded px-2 py-1 inline-block border border-forest-200 dark:border-[#235347]">
                  Context: Soil pH {soil.ph?.value || "—"}, Available N {soil.nitrogen?.value || "—"} kg/ha, OC{" "}
                  {soil.organic_carbon?.value || "—"}%
                </div>
              )}
            </div>
          </div>

          {/* User & Assistant Messages */}
          {messages.map((m, i) => (
            <div
              key={i}
              className={`flex items-start gap-3 ${m.role === "user" ? "flex-row-reverse" : "flex-row"}`}
            >
              <div
                className="flex h-8 w-8 items-center justify-center rounded-lg bg-forest-900 dark:bg-[#235347] text-white shrink-0 mt-0.5 shadow-soft"
              >
                {m.role === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
              </div>

              <div
                className={`rounded-2xl px-4 py-3 text-sm max-w-[85%] space-y-2.5 bg-soil-50 dark:bg-[#0B2B26] border border-soil-200 dark:border-[#235347] text-forest-900 dark:text-[#FFFFFF] shadow-soft ${
                  m.role === "user" ? "rounded-tr-sm" : "rounded-tl-sm"
                }`}
              >
                {/* Provenance Badge for Assistant Messages */}
                {m.role === "assistant" && (
                  <div className="flex items-center justify-between gap-2 border-b border-soil-200/60 dark:border-[#244837] pb-1.5 text-[10px]">
                    <span
                      className={`inline-flex items-center gap-1 font-semibold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                        m.isFallback
                          ? "bg-amber-100 dark:bg-amber-950/70 text-amber-900 dark:text-amber-200 border border-amber-300/60 dark:border-amber-800"
                          : "bg-forest-100 dark:bg-[#142c21] text-forest-900 dark:text-leaf-300 border border-forest-200 dark:border-forest-800"
                      }`}
                    >
                      <Sparkles className="h-3 w-3" />
                      {m.isFallback ? t("templateAnswerBadge") : t("aiAnswerBadge")}
                    </span>

                    {m.llmProvider && m.llmProvider !== "error" && (
                      <span className="font-medium text-[11px] text-soil-500 dark:text-soil-400 font-sans">
                        {m.isFallback || m.llmProvider === "template_fallback"
                          ? "AgriMind Rules Engine"
                          : "AgriMind AI Advisor"}
                      </span>
                    )}
                  </div>
                )}

                <p className="leading-relaxed whitespace-pre-line text-soil-900 dark:text-[#f2f7f4]">{m.text}</p>

                {/* Contradiction Warning */}
                {m.contradiction && (
                  <div className="rounded-lg border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/60 p-2.5 text-xs text-red-900 dark:text-red-200 font-medium flex items-center gap-2">
                    <ShieldAlert className="h-4 w-4 text-red-700 dark:text-red-400 shrink-0" />
                    <span>{m.contradiction}</span>
                  </div>
                )}

                {/* Retrieved Evidence Citations (if any) */}
                {m.evidence && m.evidence.length > 0 && (
                  <details className="text-xs text-soil-600 dark:text-soil-400 pt-1">
                    <summary className="cursor-pointer font-medium text-forest-800 dark:text-leaf-300 hover:underline inline-flex items-center gap-1 select-none">
                      <FileText className="h-3 w-3" />
                      <span>{t("retrievedEvidenceLabel")} ({m.evidence.length})</span>
                    </summary>
                    <div className="mt-2 space-y-1.5 pl-2 border-l-2 border-forest-300 dark:border-forest-700">
                      {m.evidence.slice(0, 2).map((ev, evIdx) => (
                        <div key={evIdx} className="text-[11px] bg-white/70 dark:bg-[#12221b] p-2 rounded border border-soil-200/60 dark:border-[#244837]">
                          <span className="font-semibold text-soil-800 dark:text-soil-100">
                            {ev.title || ev.source}
                          </span>
                          {ev.issuing_organization && (
                            <span className="text-soil-500 dark:text-soil-400 ml-1">[{ev.issuing_organization}]</span>
                          )}
                          <p className="text-soil-600 dark:text-soil-300 mt-0.5 italic line-clamp-2">
                            "{ev.text}"
                          </p>
                        </div>
                      ))}
                    </div>
                  </details>
                )}

                {/* Read aloud & Stop Speaking Controls */}
                {m.role === "assistant" && (
                  <div className="pt-1.5 flex items-center justify-between border-t border-soil-200/50 dark:border-[#244837]">
                    <span className="text-[10px] text-soil-500 dark:text-soil-400 font-medium uppercase">
                      {m.language ? m.language.toUpperCase() : "EN"} Response
                    </span>
                    <button
                      type="button"
                      onClick={() => speakText(m.text, i)}
                      disabled={!hasSynthesis}
                      className={`inline-flex items-center gap-1 text-xs px-2.5 py-1 rounded-md transition-colors ${
                        speakingIndex === i
                          ? "bg-red-50 dark:bg-red-950/60 text-red-800 dark:text-red-300 font-semibold border border-red-200 dark:border-red-900"
                          : "text-forest-800 dark:text-leaf-300 hover:bg-forest-50 dark:hover:bg-[#142c21] font-medium"
                      }`}
                      title={speakingIndex === i ? t("voiceStopSpeaking") : t("voiceReadAloud")}
                    >
                      {speakingIndex === i ? (
                        <>
                          <VolumeX className="h-3.5 w-3.5 text-red-600 dark:text-red-400" />
                          <span className="text-[11px]">{t("voiceStopSpeaking")}</span>
                          <span className="inline-flex gap-0.5 ml-1" aria-hidden="true">
                            <span className="h-2 w-0.5 bg-red-600 dark:bg-red-400 animate-pulse" />
                            <span className="h-3 w-0.5 bg-red-600 dark:bg-red-400 animate-pulse delay-75" />
                            <span className="h-1.5 w-0.5 bg-red-600 dark:bg-red-400 animate-pulse delay-150" />
                          </span>
                        </>
                      ) : (
                        <>
                          <Volume2 className="h-3.5 w-3.5" />
                          <span className="text-[11px]">{t("voiceReadAloud")}</span>
                        </>
                      )}
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}

          {/* Thinking / Loading Indicator */}
          {sending && (
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-forest-900 dark:bg-forest-800 text-wheat-200 shrink-0">
                <Bot className="h-4 w-4" />
              </div>
              <div className="rounded-2xl rounded-tl-sm bg-soil-50 dark:bg-[#183227] border border-soil-200/80 dark:border-[#244837] px-4 py-3 text-xs text-soil-600 dark:text-soil-300 flex items-center gap-2">
                <span className="flex items-center gap-1" aria-hidden="true">
                  <i className="typing-dot h-1.5 w-1.5 rounded-full bg-forest-700 dark:bg-leaf-400" />
                  <i className="typing-dot h-1.5 w-1.5 rounded-full bg-forest-700 dark:bg-leaf-400" />
                  <i className="typing-dot h-1.5 w-1.5 rounded-full bg-forest-700 dark:bg-leaf-400" />
                </span>
                <span>{t("chatThinking")}</span>
              </div>
            </div>
          )}
        </div>

        {/* Suggested Question Chips */}
        <div className="border-t border-soil-200 dark:border-[#235347] bg-soil-50 dark:bg-[#0B2B26] px-4 py-2.5 flex items-center gap-2 overflow-x-auto text-xs">
          <span className="text-[11px] text-soil-600 dark:text-[#8EB69B] shrink-0 font-medium">Suggested:</span>
          {suggestions.map((q, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleSend(q)}
              className="rounded-full border border-soil-200 dark:border-[#235347] bg-white dark:bg-[#163832] px-3 py-1 text-xs text-forest-900 dark:text-[#FFFFFF] hover:bg-soil-100 dark:hover:bg-[#235347] shrink-0 transition-colors"
            >
              {q}
            </button>
          ))}
        </div>

        {/* Transcript Ready Notification / Correction Banner */}
        {transcriptReady && (
          <div className="border-t border-forest-200 dark:border-forest-700 bg-forest-50/70 dark:bg-forest-950/70 px-4 py-2 flex items-center justify-between text-xs text-forest-900 dark:text-forest-100">
            <div className="flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5 text-forest-700 dark:text-leaf-400 shrink-0" />
              <span>{t("voiceTranscriptReady")}</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => handleSend()}
                className="font-semibold text-forest-800 dark:text-leaf-300 hover:text-forest-950 dark:hover:text-white underline text-[11px]"
              >
                {t("chatSend")}
              </button>
              <button
                type="button"
                onClick={() => {
                  setInput("");
                  setTranscriptReady(false);
                }}
                className="text-soil-500 dark:text-soil-400 hover:text-soil-800 dark:hover:text-white text-[11px]"
              >
                Clear
              </button>
            </div>
          </div>
        )}

        {/* Active Listening / Recording State Banner */}
        {speechState === "listening" && (
          <div className="border-t border-red-200 dark:border-red-800 bg-red-50/80 dark:bg-red-950/70 px-4 py-2.5 flex items-center justify-between text-xs text-red-900 dark:text-red-200">
            <div className="flex items-center gap-2">
              <span className="flex h-2.5 w-2.5 rounded-full bg-red-600 animate-ping" />
              <span className="font-semibold">{t("micListening")} ({languageDisplayName})</span>
            </div>
            <button
              type="button"
              onClick={cancelListening}
              className="inline-flex items-center gap-1 text-[11px] text-red-800 dark:text-red-300 hover:text-red-950 dark:hover:text-white font-medium underline"
            >
              <X className="h-3 w-3" />
              <span>{t("voiceCancelListening")}</span>
            </button>
          </div>
        )}

        {/* Active Processing State Banner */}
        {speechState === "processing" && (
          <div className="border-t border-amber-200 dark:border-amber-800 bg-amber-50/80 dark:bg-amber-950/70 px-4 py-2 text-xs text-amber-900 dark:text-amber-200 flex items-center gap-2">
            <RefreshCw className="h-3.5 w-3.5 text-amber-700 dark:text-amber-400 animate-spin" />
            <span>{t("micProcessing")}</span>
          </div>
        )}

        {/* Input Bar */}
        <div className="border-t border-soil-200 dark:border-[#235347] p-3 sm:p-4 bg-white dark:bg-[#163832] flex items-center gap-2">
          {/* Main Microphone Button */}
          <button
            type="button"
            onClick={speechState === "listening" ? cancelListening : startListening}
            disabled={!hasRecognition}
            aria-label={speechState === "listening" ? t("voiceCancelListening") : t("micStart")}
            className={`rounded-xl p-2.5 sm:p-3 transition-all relative ${
              speechState === "listening"
                ? "bg-red-600 text-white shadow-md ring-4 ring-red-200 dark:ring-red-900 animate-pulse"
                : speechState === "processing"
                ? "bg-amber-500 text-white"
                : "border border-soil-200 dark:border-[#235347] bg-soil-50 dark:bg-[#0B2B26] text-forest-800 dark:text-[#DAF1DE] hover:bg-soil-100 dark:hover:bg-[#235347]"
            } disabled:opacity-40 disabled:cursor-not-allowed`}
            title={
              !hasRecognition
                ? t("voiceNotSupported")
                : speechState === "listening"
                ? t("voiceCancelListening")
                : `${t("micStart")} (${languageDisplayName})`
            }
          >
            {speechState === "listening" ? (
              <MicOff className="h-5 w-5" />
            ) : (
              <Mic className="h-5 w-5" />
            )}
          </button>

          {/* Editable Text Input */}
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              if (transcriptReady) setTranscriptReady(false);
            }}
            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && handleSend()}
            placeholder={
              speechState === "listening"
                ? t("micListening")
                : speechState === "processing"
                ? t("micProcessing")
                : t("chatInputPlaceholder")
            }
            className="flex-1 rounded-xl border border-soil-200 dark:border-[#235347] px-3.5 py-2.5 text-sm bg-white dark:bg-[#0B2B26] text-forest-900 dark:text-[#FFFFFF] placeholder:text-soil-400 dark:placeholder:text-[#8EB69B] focus:border-forest-700 dark:focus:border-[#8EB69B] focus:ring-1 focus:ring-forest-700 dark:focus:ring-[#8EB69B] transition-all"
          />

          {/* Send Button */}
          <button
            type="button"
            onClick={() => handleSend()}
            disabled={sending || !input.trim()}
            className="inline-flex items-center justify-center rounded-xl bg-forest-900 dark:bg-[#235347] p-2.5 sm:px-4 sm:py-2.5 text-white text-sm font-medium hover:bg-forest-800 dark:hover:bg-[#2E6B5C] disabled:opacity-40 disabled:cursor-not-allowed transition-all shadow-xs"
            aria-label={t("chatSend")}
          >
            <Send className="h-4 w-4" />
            <span className="hidden sm:inline sm:ml-1.5">{t("chatSend")}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
