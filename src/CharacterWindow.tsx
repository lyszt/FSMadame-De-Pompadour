import { useState, useEffect } from 'react';

// Define the shape of the character object
interface Character {
    id: string;
    name: string;
}

// Define the props for the CharacterWindow component
interface CharacterWindowProps {
    char: Character;
    setActiveChar: (char: Character | null) => void;
}

function CharacterWindow({ char, setActiveChar }: CharacterWindowProps) {
    const [personality, setPersonality] = useState<string>('');
    const [backstory, setBackstory] = useState<string>('');
    const [wants, setWants] = useState<string[]>([]);
    const [fears, setFears] = useState<string[]>([]);
    const [isLoading, setIsLoading] = useState<boolean>(true);

    useEffect(() => {
        if (!char?.id) return;

        async function getCharInfo() {
            setIsLoading(true);
            try {
                const response = await fetch('http://127.0.0.1:5000/get_character_details', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id_number: char.id })
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }

                const details = await response.json();
                console.log(`Details for character ${char.id}:`, details);

                setPersonality(details.personality?.join(', ') || 'N/A');
                setBackstory(details.backstory || 'N/A');
                setWants(details.wants || []);
                setFears(details.fears || []);

            } catch (error) {
                console.error("Error fetching character details:", error);
                setPersonality('Error loading details.');
            } finally {
                setIsLoading(false);
            }
        }

        getCharInfo();
    }, [char]);

    return (
        <div className="w-full bg-slate-800 text-slate-200 flex flex-col items-start pb-5 justify-center z-20 handle shadow-lg border-t-2 border-cyan-400">
            <div className="bg-slate-900 w-full flex flex-row items-center relative p-2">
                <h3 className="text-lg font-bold text-cyan-400">{char.name}</h3>
                <button
                    className="p-2 bg-red-500 h-full w-10 font-bold flex items-center justify-center text-white hover:bg-red-600 absolute right-0 top-0"
                    onClick={() => setActiveChar(null)}
                >
                    X
                </button>
            </div>

            <div className="p-4 w-full">
                {isLoading ? (
                    <p>Loading details...</p>
                ) : (
                    <div className="space-y-4">
                        <div>
                            <h4 className="font-semibold text-cyan-500 mb-1">Personality Traits</h4>
                            <p className="text-sm italic">{personality}</p>
                        </div>

                        <div>
                            <h4 className="font-semibold text-cyan-500 mb-1">Backstory</h4>
                            <p className="text-sm">{backstory}</p>
                        </div>

                        <div>
                            <h4 className="font-semibold text-cyan-500 mb-1">Wants</h4>
                            <ul className="list-disc list-inside text-sm space-y-1">
                                {wants.map((want, index) => <li key={index}>{want}</li>)}
                            </ul>
                        </div>

                        <div>
                            <h4 className="font-semibold text-cyan-500 mb-1">Fears</h4>
                            <ul className="list-disc list-inside text-sm space-y-1">
                                {fears.map((fear, index) => <li key={index}>{fear}</li>)}
                            </ul>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default CharacterWindow;
