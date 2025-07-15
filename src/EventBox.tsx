import { useState, createElement, useEffect, useRef } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'

function EventBox() {

    const [dialogues, setDialogues] = useState<string[]>([
        'Welcome to Humanity Simulator.',
    ]);

    const scrollContainerRef = useRef(null);
    useEffect(() => {
        const node = scrollContainerRef.current;
        if(node) {
            node.scrollTop = node.scrollHeight;
        }
    }, [dialogues]);

    async function runTurn(e: React.MouseEvent<HTMLButtonElement>) {
        e.preventDefault();
        const url = "http://127.0.0.1:5000/action"
        try {
            const response = await fetch(url, {
                method: 'GET',
            })
            if (!response.ok) {
                throw new Error(`Response status: ${response.status}`);
            }
            const json: { body: string; status: number } = await response.json();
            setDialogues(prev => [...prev, json.body]);
        } catch (error) {
            if (error instanceof Error) {
                const message = error.message;
                console.error(message);
            }
        }

    }

  return (
      <div className="w-3/5 h-4/5 bg-stone-900 m-10 relative">
          <div ref={scrollContainerRef} className="eventBox w-full h-full">
              {dialogues.map((text, i) => (
                  <p key={i} className="dialogue_box">
                      {text}
                  </p>
              ))}

          </div>
          <div className="absolute bottom-0 pt-10 w-full h-1/4">
              <div className="w-full h-full bg-stone-500 flex flex-row">
                  <button type="button" onClick={runTurn} className="pr-10 pl-10 hover:bg-stone-800 bg-stone-950">Next
                      turn
                  </button>
              </div>
          </div>
      </div>
  )
}

export default EventBox
