import { useState, createElement, useEffect, useRef } from 'react'
import ambienceAudio from './assets/audio/ambience.mp3'
import CharacterWindow from './CharacterWindow.tsx';
import Draggable from 'react-draggable';
import './App.css'

function EventBox() {
    const nodeRef = useRef(null);
    const [dialogues, setDialogues] = useState<string[]>([
        'Booting simulation... Welcome to the FS Madame de Pompadour.',
    ]);

    const [characterList, setCharacterList] = useState<{ id: string; name: string }[]>([]);
    const [activeChar, setActiveChar] = useState<{ id: string; name: string } | null>(null);

    function openCharWindow(char: { id: string; name: string; }){
        setActiveChar(char)
    }

    useEffect(() => {
        async function loadCharacterList() {
            const url = "http://127.0.0.1:5000/get_actors";
            try {
                const response = await fetch(url, { method: 'GET' });
                if (!response.ok) {
                    throw new Error(`Response status: ${response.status}`);
                }
                const json: { body: Record<string, string>; status: number } = await response.json();
                const characters = Object.entries(json.body).map(
                    ([id, name]) => ({ id, name })
                );
                setCharacterList(characters);

            } catch (error) {
                const message = (error instanceof Error) ? error.message : "Unknown error";
                console.error(message);
                setDialogues(prev => [...prev, `[SYSTEM ERROR] Failed to load character manifest: ${message}`]);
            }
        }
        loadCharacterList();
    }, []);

    const scrollContainerRef = useRef<HTMLDivElement>(null);
    useEffect(() => {
        const node = scrollContainerRef.current;
        if(node) {
            node.scrollTop = node.scrollHeight;
        }
    }, [dialogues]);

    const ambienceAudioRef = useRef<HTMLAudioElement | null>(null);
    const hasStartedAmbience = useRef(false);

    async function runTurn(e: React.MouseEvent<HTMLButtonElement>) {
        e.preventDefault();

        if (!hasStartedAmbience.current) {
            ambienceAudioRef.current = new Audio(ambienceAudio);
            ambienceAudioRef.current.loop = true;
            ambienceAudioRef.current.volume = 0.1;
            ambienceAudioRef.current.play().catch((err) => {
                console.warn('Ambience audio playback failed:', err);
            });
            hasStartedAmbience.current = true;
        }
        let debug = false;
        try {
            const url = "http://127.0.0.1:5000/action"
            const audio = new Audio('src/assets/audio/click.mp3');
            audio.play();

            const response = await fetch(url, { method: 'GET' });
            if (!response.ok) {
                throw new Error(`Response status: ${response.status}`);
            }
            const json: {
                debug: boolean;
                body: string; status: number } = await response.json();
            setDialogues(prev => [...prev, json.body]);
            const text = json.body;
            debug = json.debug;
            // Generate TTS
            const tts_url = "http://127.0.0.1:5000/text_to_speech";
            const res = await fetch(tts_url, {
                method: 'POST',
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text })
            });
            if (!res.ok) {
                throw new Error(`Server error: ${res.status}`);
            }
            const blob = await res.blob();
            const voice_url = URL.createObjectURL(blob);
            const voiced_text = new Audio(voice_url);
            voiced_text.play().catch(err => console.error("Audio playback error:", err));
        } catch (error) {
            if(!debug) {
                const message = (error instanceof Error) ? error.message : "Unknown error";
                console.error(message);
                setDialogues(prev => [...prev, `[SYSTEM ERROR] Action failed: ${message}`]);
            }
        }
    }

    return (
        <div className="w-full h-screen bg-[#0a101f] p-4 flex flex-row font-mono">
            {/* Left Panel: Event Box */}
            <div ref={scrollContainerRef} className="eventBox w-3/4 h-full">
                {dialogues.map((text, i) => (
                    <p key={i} className="dialogue_box">
                        {text}
                    </p>
                ))}
                <button type="button" onClick={runTurn}
                        className="passTurn w-1/10 fixed right-5 bottom-5 flex justify-center items-center flex-col">
                    <img className="w-1/5" src="src/assets/icons/arrow.svg" alt="Pass turn"/>
                    <span className="text-lg font-bold uppercase">Next</span>
                </button>
            </div>

            {/* Right Panel: Controls and Character List */}
            <div className="w-1/4 h-full p-4">
                <div className="w-full h-full flex flex-col items-center justify-start">
                    <h3 className="text-cyan-400 uppercase tracking-widest text-center mb-2">Crew Manifest</h3>
                    <div className="w-full h-3/4 bg-black/50 characterList select-none">
                        {characterList.map((char) => (
                            <button key={char.id} id={char.id} className="text-white" onClick={() => openCharWindow(char)}>
                                {char.name}
                            </button>
                        ))}
                    </div>

                    {activeChar && (
                        <Draggable handle=".handle" nodeRef={nodeRef}>
                            <div ref={nodeRef} className="absolute left-1/3 top-1/4 w-1/3 z-50">
                                <CharacterWindow char={activeChar} setActiveChar={setActiveChar} />
                            </div>
                        </Draggable>
                    )}


                </div>
            </div>
        </div>
    )
}

export default EventBox
