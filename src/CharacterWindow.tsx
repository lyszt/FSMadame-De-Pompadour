import { useState, useEffect, useRef } from 'react';

function CharacterWindow({ char, setActiveChar }) {
    const [personalityField, setPersonalityField] = useState('');

    useEffect(() => {
        if (!char?.id) return;

        async function getCharInfo() {
            try {
                const response = await fetch('http://127.0.0.1:5000/get_personality', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id_number: char.id })
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }

                const personalityTraits = await response.json();
                console.log(`Personality for character ${char.id}:`, personalityTraits);

                if (personalityTraits) {
                    setPersonalityField(personalityTraits.join(', '));
                }
            } catch (error) {
                console.error("Error fetching character personality:", error);
            }
        }

        getCharInfo();
    }, [char]);

    return (
            <div className="w-[100%] bg-cyan-200 text-stone-900 flex flex-col items-start pb-5 justify-center z-20 handle">
                <div className="bg-cyan-500 w-full options flex flex-row items-center relative p-2">
                    <h3 className="p-2bg-cyan-300  w-full text-[1em]">{char.name}</h3>
                    <button className="p-2 bg-red-400 h-full w-1/8 font-bold
                     flex items-center justify-center text-white hover:bg-red-500 absolute right-0"
                    onClick={() => setActiveChar(null)}
                    >X</button>
                </div>
                <p className="ml-3 mt-3 pr-5">{personalityField}</p>
            </div>
    );
}

export default CharacterWindow;
