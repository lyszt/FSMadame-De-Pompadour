import { useState, useEffect } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import EventBox from './EventBox.tsx'

function App() {
  const [count, setCount] = useState(0)
  return (
      <main className="w-screen h-screen flex flex-col items-center justify-start">
          <div className="w-full h-full flex flex-col  justify-center">
            <span className="text-black text-2xl ml-2 mb-4">French Ship Madame de Pompadour: The human experience social simulation</span>
            <EventBox/>
          </div>
      </main>
  )
}

export default App
