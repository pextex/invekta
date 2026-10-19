import { useEffect, useRef, useState } from "react";
import { ArrowLeft, ArrowRight, Maximize2, Minimize2, MousePointer2, Pause, Play, RotateCcw, Volume2, X } from "lucide-react";
import { nextTourPosition, previousTourPosition, tourLessons } from "./tourLessons";
import { getTourNarration } from "./tourOpenings";
import "./appTour.css";

type Props = { organization?: string; page: string; onPage: (page: string) => void; canViewHistory: boolean; canManageUsers: boolean; onClose: () => void };
type Box = { top: number; left: number; width: number; height: number };
export default function AppTour({ organization, page, onPage, canViewHistory, canManageUsers, onClose }: Props) {
  const lessons = tourLessons(organization, canViewHistory, canManageUsers);
  const [lessonId, setLessonId] = useState<string | null>(null);
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(true);
  const [narration, setNarration] = useState(true);
  const [auto, setAuto] = useState(true);
  const [minimized, setMinimized] = useState(false);
  const [repeat, setRepeat] = useState(0);
  const [box, setBox] = useState<Box | null>(null);
  const [waiting, setWaiting] = useState(false);
  const [speechError, setSpeechError] = useState(false);
  const [finished, setFinished] = useState(false);
  const [narrationEnded, setNarrationEnded] = useState(false);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const panelRef = useRef<HTMLElement>(null);
  const navigateRef = useRef(onPage);
  navigateRef.current = onPage;
  const closeRef = useRef(onClose);
  closeRef.current = onClose;
  const lesson = lessons.find(item => item.id === lessonId);
  const step = lesson?.steps[index];
  const nextPosition = nextTourPosition(lessons, lessonId, index);
  const previousPosition = previousTourPosition(lessons, lessonId, index);
  const compact = !!lesson && !finished && minimized;
  const audioSource = getTourNarration(lesson, index);

  useEffect(() => {
    const previous = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    panelRef.current?.focus();
    const key = (event: KeyboardEvent) => { if (event.key === "Escape") { event.preventDefault(); closeRef.current(); } };
    window.addEventListener("keydown", key);
    return () => { window.removeEventListener("keydown", key); previous?.focus(); };
  }, []);
  useEffect(() => {
    if (!step || finished) return;
    navigateRef.current(step.page);
  }, [step?.page, lessonId, index, repeat, finished]);

  // Wait for async page content, then keep the marker aligned while scrolling/resizing.
  useEffect(() => {
    setBox(null);
    if (!step || finished || page !== step.page) return;
    setWaiting(true);
    let target: HTMLElement | null = null;
    let frame = 0;
    const update = () => {
      if (!target?.isConnected) return;
      const r = target.getBoundingClientRect();
      if (r.width && r.height) setBox({ top: r.top - 5, left: r.left - 5, width: r.width + 10, height: r.height + 10 });
    };
    const position = () => { cancelAnimationFrame(frame); frame = requestAnimationFrame(update); };
    const resize = new ResizeObserver(position);
    const locate = () => {
      const next = document.querySelector<HTMLElement>(step.target);
      if (next && next !== target) {
        if (target) resize.unobserve(target);
        target = next;
        target.scrollIntoView({ block: "center", inline: "nearest", behavior: "instant" });
        resize.observe(target); setWaiting(false); position();
      } else if (!next && target) { resize.unobserve(target); target = null; setBox(null); setWaiting(true); }
    };
    const content = document.querySelector("[data-tour-content]");
    const observer = new MutationObserver(locate);
    if (content) observer.observe(content, { childList: true, subtree: true });
    locate();
    window.addEventListener("resize", position);
    window.addEventListener("scroll", position, true);
    return () => { observer.disconnect(); resize.disconnect(); cancelAnimationFrame(frame); window.removeEventListener("resize", position); window.removeEventListener("scroll", position, true); };
  }, [step?.target, step?.page, page, index, lessonId, repeat, finished]);

  useEffect(() => {
    setNarrationEnded(false); setSpeechError(false);
    if (!audioSource || finished || page !== step?.page) return;
    const audio = new Audio(audioSource);
    audio.preload = "auto";
    audioRef.current = audio;
    audio.onended = () => setNarrationEnded(true);
    audio.onerror = () => setSpeechError(true);
    return () => {
      audio.onended = null; audio.onerror = null; audio.pause();
      audio.removeAttribute("src"); audio.load();
      if (audioRef.current === audio) audioRef.current = null;
    };
  }, [audioSource, finished, page, step?.page, repeat]);

  useEffect(() => {
    const audio = audioRef.current;
    if (!audio) return;
    let active = true;
    if (playing && narration && !audio.ended) {
      audio.play().then(() => { if (active) setSpeechError(false); }).catch(() => { if (active) setSpeechError(true); });
    } else audio.pause();
    return () => { active = false; audio.pause(); };
  }, [playing, narration, audioSource, finished, page, step?.page, repeat]);

  useEffect(() => {
    if (!step || finished || !playing || !auto || page !== step.page) return;
    const textOnly = !narration || !audioSource || speechError;
    if (!textOnly && !narrationEnded) return;
    const timer = setTimeout(() => {
      if (nextPosition) {
        if (nextPosition.lessonId !== lessonId) setMinimized(true);
        setLessonId(nextPosition.lessonId); setIndex(nextPosition.index);
      } else setFinished(true);
    }, textOnly ? Math.max(8000, step.text.split(/\s+/).length * 500) : 1800);
    return () => clearTimeout(timer);
  }, [step?.text, step?.page, finished, playing, auto, page, narration, audioSource, speechError, narrationEnded, lessonId, nextPosition?.lessonId, nextPosition?.index]);

  function start(id: string) { setLessonId(id); setIndex(0); setFinished(false); setPlaying(true); setMinimized(true); setRepeat(value => value + 1); }
  function next() {
    if (nextPosition) {
      if (nextPosition.lessonId !== lessonId) setMinimized(true);
      setLessonId(nextPosition.lessonId); setIndex(nextPosition.index);
    } else setFinished(true);
  }
  function previous() { if (previousPosition) { setLessonId(previousPosition.lessonId); setIndex(previousPosition.index); } }
  const nextLabel = !nextPosition ? "Završi vodič" : nextPosition.lessonId !== lessonId ? "Sledeća lekcija" : "Sledeći korak";
  return <>
    {step && !finished && box && <div className="tour-markers" aria-hidden="true">
      <div className="tour-highlight" style={box} />
      <MousePointer2 className="tour-pointer" size={36} fill="#2563eb" stroke="white" style={{ top: Math.max(8, Math.min(window.innerHeight - 48, box.top + Math.min(box.height / 2, 60))), left: Math.max(8, Math.min(window.innerWidth - 44, box.left + Math.min(box.width - 16, 80))) }} />
    </div>}
    <section className={`app-tour${compact ? " app-tour-minimized" : ""}`} role="dialog" aria-modal="false" aria-labelledby="tour-title" ref={panelRef} tabIndex={-1}>
      <header><span><MousePointer2 size={17} />{compact ? <span><strong id="tour-title">{lesson?.title}</strong><small>{step?.title} · {index + 1}/{lesson?.steps.length}</small></span> : "Vodič kroz aplikaciju"}</span><div className="tour-header-actions">
        {lesson && !finished && <button type="button" aria-label={compact ? "Proširi vodič" : "Minimizuj vodič"} onClick={() => setMinimized(value => !value)}>{compact ? <Maximize2 size={17} /> : <Minimize2 size={17} />}</button>}
        <button type="button" aria-label="Zatvori vodič" onClick={onClose}><X size={19} /></button></div></header>
      {!lesson ? <>
        <h2 id="tour-title">Šta želite da naučite?</h2>
        <p>Izaberite karticu od koje želite da počnete. Vodič zatim automatski nastavlja kroz ostale dostupne lekcije. Pokazivač će pratiti elemente aplikacije uz objašnjenje na srpskom. Vodič otvara ekrane, a unos i čuvanje podataka ostaju vama. Pre početka sačuvajte otvoren unos ili kopirajte pripremljeni mejl.</p>
        <button type="button" className="tour-next tour-start" onClick={() => start(lessons[0].id)}><Play size={16} />Pokreni vodič od početka</button>
        <div className="tour-lessons">{lessons.map(item => <button type="button" key={item.id} onClick={() => start(item.id)}>{item.title}<ArrowRight size={16} /></button>)}</div>
      </> : finished ? <>
        <h2 id="tour-title">Vodič je završen</h2><p>Stigli ste do kraja dostupnih lekcija. Možete ponoviti poslednju lekciju ili izabrati karticu od koje želite ponovo da počnete.</p>
        <div className="tour-actions"><button type="button" onClick={() => start(lesson.id)}><RotateCcw size={15} />Ponovi lekciju</button><button type="button" onClick={() => setLessonId(null)}>Sve lekcije</button></div>
      </> : step && compact ? <>
        {(!audioSource || speechError) && <p className="tour-caption" aria-live="polite">{step.text}</p>}
        <div className="tour-compact-controls">
          <button type="button" aria-label="Prethodni korak" disabled={!previousPosition} onClick={previous}><ArrowLeft size={16} /></button>
          <button type="button" onClick={() => setPlaying(value => !value)}>{playing ? <Pause size={16} /> : <Play size={16} />}{playing ? "Pauza" : "Nastavi"}</button>
          <button type="button" aria-label="Ponovi korak" onClick={() => { setPlaying(true); setRepeat(value => value + 1); }}><RotateCcw size={16} /></button>
          <button type="button" className="tour-next" aria-label={nextLabel} onClick={next}><ArrowRight size={16} /></button>
        </div>
        {speechError && <small role="status">Zvuk nije pokrenut. Pritisnite Ponovi korak.</small>}
      </> : step && <>
        <div className="tour-progress">{lesson.title} · Korak {index + 1} od {lesson.steps.length}</div>
        <h2 id="tour-title">{lesson.title}</h2><h3 className="tour-step-title">{step.title}</h3><p aria-live="polite">{step.text}</p>
        {waiting && <small className="tour-note">Element trenutno nije prikazan. Sačekajte učitavanje, ponovite korak ili ga preskočite.</small>}
        <div className="tour-actions">
          <button type="button" onClick={() => setPlaying(value => !value)}>{playing ? <Pause size={15} /> : <Play size={15} />}{playing ? "Pauza" : "Nastavi"}</button>
          <button type="button" onClick={() => { setPlaying(true); setRepeat(value => value + 1); }}><RotateCcw size={15} />Ponovi korak</button>
          <button type="button" onClick={() => setLessonId(null)}>Sve lekcije</button>
        </div>
        <div className="tour-options"><label><input type="checkbox" checked={narration} disabled={!audioSource} onChange={event => setNarration(event.target.checked)} /><Volume2 size={15} />Naracija</label><label><input type="checkbox" checked={auto} onChange={event => setAuto(event.target.checked)} />Automatski prelazi</label></div>
        {audioSource && <small className="tour-note">AI naracija · ženski glas na srpskom.</small>}
        {(!audioSource || speechError) && <small className="tour-note" role="status">{!audioSource ? "Za ovaj korak je trenutno dostupno tekstualno uputstvo. Ostale snimljene korake prati ženski glas na srpskom." : "Zvuk nije pokrenut. Pritisnite Ponovi korak ili pratite tekst."}</small>}
        <footer><button type="button" disabled={!previousPosition} onClick={previous}><ArrowLeft size={15} />Nazad</button><button type="button" onClick={next}>Preskoči</button><button type="button" className="tour-next" onClick={next}>{nextLabel}<ArrowRight size={15} /></button></footer>
      </>}
    </section>
  </>;
}
