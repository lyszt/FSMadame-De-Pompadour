# FS Madame de Pompadour
## Spaceship simulator using AI and random actions inspired by Star Trek.
---

FS Madame de Pompadour is a text-based narrative simulator that creates dynamic and unpredictable stories set in a sci-fi universe. By clicking "Next," you advance the simulation one turn at a time, watching as a cast of characters interact with each other based on a combination of predefined behaviors and generative AI.

The goal is to create a "digital terrarium" where complex social dynamics and unexpected events emerge from simple rules and the creative power of AI.

``` 
Welcome to FS Madame de Pompadour.

Crewman Claire tries to hold their breath for as long as possible.

Crewman Brock turns to face a control panel, pointedly ignoring Crewman Aldric.

Crewman Case acknowledges... with a single click over the comms channel Crewman Claire.

Crewman Reginauld shrugs, then continues polishing the already gleaming brass handrail.

Crewman Halvard uses a corporate logo for target practice with a low-power laser.

Crewman Torre gives a thumbs-up that doesn't quite reach their eyes to Crewman Aldric.

Crewman Sonny sighs, then heads towards the mess hall for a lukewarm ration of reconstituted beef.

Crewman Ignatius listens to garbled transmissions on the long-range comms.

Crewman Ignatius answers a complex question from... with a simple "it's nominal" Crewman Arvie.

Crewman Sonny joins the queue for the mess hall, muttering about the lukewarm beef.

Crewman Halvard directs a question to the group, while looking away from Crewman Reginauld.

Crewman Sonny tosses a wrench up and catches it in zero-g.

Crewman Case tidies their personal sleeping quarters.

Crewman Claire heads towards the mess hall, hoping the lukewarm beef isn't as bad as Sonny said.

```
Of course. Scrapping the previous analysis and focusing on a "tech demo" style gives it a completely different energy. The goal is to showcase the simulation's capabilities by using the character actions as evidence of a dynamic, underlying system.

Here is the revised text, presented as a single, flowing description.

In this demonstration snapshot from the FS Madame de Pompadour simulation, we observe a complex and dynamic social ecosystem in motion. The system showcases its capacity for generating emergent narrative not through pre-scripted events, but by allowing independent agents to interact, creating a rich and believable tapestry of life on the lower decks.

Notice the subtle social friction demonstrated between several crewmembers. Crewman Brock pointedly turns to a control panel to ignore Crewman Aldric, a clear, non-verbal sign of conflict. This tension is immediately recognized and escalated by Crewman Torre, whose simulation generates a thumbs-up that "doesn't quite reach their eyes"—a perfect example of nuanced, passive-aggressive behavior arising organically. At the same time, we see Crewman Halvard directing a question to the group while deliberately avoiding eye contact with Crewman Reginauld, hinting at another underlying social dynamic.

While this quiet drama unfolds, the simulation highlights individual personalities through environmental interaction. Halvard displays a rebellious streak, using a low-power laser for target practice on a corporate logo. In contrast, Reginauld meticulously polishes an already gleaming handrail, suggesting a detail-oriented or dutifully bored nature. These are not random actions; they are behaviors selected by the engine that paint a picture of character through action alone. We also see crewmembers engaged in mundane, grounding activities—Sonny idly tossing a wrench in zero-g, Claire testing her breath-holding capacity, and Case tidying their personal quarters.

Crucially, the simulation demonstrates a persistent world with clear cause and effect. Crewman Sonny's initial sigh and complaint about the "lukewarm ration of reconstituted beef" becomes a piece of information in the environment. This directly informs a later action from Crewman Claire, whose motivation for heading to the mess hall is explicitly tied to hoping the food isn't as bad as Sonny claimed.

Finally, the system showcases distinct role-based behaviors. Crewman Ignatius is depicted as a focused technician, listening to garbled long-range transmissions and answering a complex question from Crewman Arvie with a terse, professional "it's nominal." His actions, alongside Crewman Case's clipped, single-click comms acknowledgement, illustrate how the engine can produce different flavors of interaction based on a character's implicit role. This brief window reveals a powerful engine for emergent storytelling, where social dynamics, character quirks, and direct causal chains arise naturally from the interaction of AI-driven agents within a shared environment.

FS Madame de Pompadour is built on a modern, decoupled web architecture, separating the backend simulation engine from the frontend user interface for modularity and performance.

### Backend: Python, Flask, and Gemini

The entire simulation core and logic resides in the Python backend.

* **Python:** The natural choice for its powerful data handling and robust AI/ML ecosystem. The object-oriented approach allows for modular `Crewman` and `ActorManager` classes that are easy to extend.
* **Flask:** A lightweight and flexible web framework used to create the API that the frontend communicates with. Its sole responsibility is to receive a request for the next turn, trigger the simulation logic, and return the result.
* **Google Gemini:** The "ghost in the machine." The project integrates with the Gemini API to power its intelligent action system. When a character decides to act "intelligently," the backend sends a prompt—containing the context of the ship, the character's role, and the recent action history—to the Gemini model, which then returns a creative, context-aware action.

### Frontend: React, Vite, and Tailwind CSS

The user interface is a fast, modern single-page application (SPA).

* **React:** A powerful JavaScript library for building dynamic and component-based user interfaces. The entire event log is a React component that efficiently updates as new actions are received from the backend.
* **Vite:** A next-generation frontend build tool that provides an extremely fast development server and optimized production builds.
* **TypeScript:** Used to add static typing to the JavaScript code, improving developer experience and reducing bugs.
* **Tailwind CSS:** A utility-first CSS framework that allows for rapid and consistent styling directly within the HTML, as seen in the component's class names.

### Overall Architecture

The flow of a single turn is simple and effective:

1.  The user clicks the **"Next"** button in the React-based UI.
2.  The frontend sends a `fetch` request to the backend's `/action` endpoint running on Flask.
3.  The Flask server calls the Python `ActorManager`, which runs a single turn of the simulation, potentially calling the Gemini API.
4.  The backend returns the resulting action string as a JSON object.
5.  The React frontend receives the JSON, updates its state, and renders the new event on the screen, automatically scrolling to the latest entry.



