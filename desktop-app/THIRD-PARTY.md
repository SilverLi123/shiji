# Third-party code in this application

React Bits by David Haz (Copyright 2026), MIT + Commons Clause.
Original repository: https://github.com/DavidHDev/react-bits
Pinned commit: 4d6a46d3f401736695c495f1e72ed429e0ed1b93

`static/resource-bits.js` adapts Masonry shortest-column placement, AnimatedContent bounded reveal Magnet center-distance offsets and Dock distance-based magnification and TiltedCard centered pointer rotation from:
- src/content/Components/Masonry/Masonry.jsx
- src/content/Animations/AnimatedContent/AnimatedContent.jsx
- src/content/Animations/Magnet/Magnet.jsx
- src/content/Components/Dock/Dock.jsx
- src/content/Components/Dock/Dock.css
- src/content/Components/TiltedCard/TiltedCard.jsx
- src/content/Components/TiltedCard/TiltedCard.css

Adaptations replace React hooks and GSAP with native DOM, ResizeObserver and Web Animations; add interrupted animation cleanup, capped stagger, reduced-motion and touch behavior, measured caption height, and host metadata controls. Dock replaces motion/react with native pointer events and CSS transitions; magnifies only icons to preserve labels and hit targets, and uses persistent labels instead of hover-only tooltips. TiltedCard replaces motion/react springs with CSS transitions, caps rotation at 3 degrees and scale at 1.06, and rotates only loaded preview images inside stable buttons. It is disabled for full-image fitting, touch, keyboard focus and reduced motion, with reset on pointer leave, scroll, layout, blur and preference changes. Components are integrated into the resource-library application, not distributed as a standalone component library.

Full copyright and license notice: `static/licenses/react-bits.md`.

MotionSites AI (https://motionsites.ai/) and Recent (https://www.recent.co/) informed gallery categorization and image/caption hierarchy. No template code, prompts or branded artwork from those sites were copied into the interface. The five captured website preview images remain the existing resource display fallbacks.

Lucide tag icon: https://github.com/lucide-icons/lucide/blob/main/icons/tag.svg ; ISC license and copyright notice in static/icons/LICENSE.
