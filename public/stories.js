const sampleStories = [
  {
    category: 'AI',
    title: 'AI agents move from prompts to complete tasks',
    deck: 'New assistants are being designed to plan work across apps, then pause for people when a decision needs them.',
    happened: 'AI tools are beginning to connect several steps into one guided workflow.',
    matters: 'The test for agents is shifting from clever answers to dependable work.',
    image: 'assets/swipe-robotics.jpg',
    imageAlt: 'A humanoid robot working beside people on a factory floor',
    imagePosition: 'center 34%',
  },
  {
    category: 'Tech business',
    title: 'The AI race now runs through the data center',
    deck: 'Cloud companies are expanding server capacity as demand for advanced models rises.',
    happened: 'Infrastructure spending is growing alongside investment in new AI models.',
    matters: 'Compute access is becoming a competitive advantage for the whole industry.',
    image: 'assets/swipe-data-center.jpg',
    imageAlt: 'A technician walking through a blue-lit data center',
    imagePosition: 'center 42%',
  },
  {
    category: 'Technology',
    title: 'Robots take on more work beside human teams',
    deck: 'Manufacturers are testing machines on practical jobs that once depended on repetitive manual work.',
    happened: 'More robotics pilots are moving from controlled demos into everyday workplaces.',
    matters: 'Reliable performance on ordinary shifts will decide whether adoption grows.',
    image: 'assets/swipe-robotics.jpg',
    imageAlt: 'A humanoid robot and technicians working together in a factory',
    imagePosition: 'center 72%',
  },
  {
    category: 'Founders & startups',
    title: 'Smaller teams build products at a faster pace',
    deck: 'Lower-cost software and AI tools help founders test an idea before committing to a full launch.',
    happened: 'Startups are using lightweight prototypes to learn from customers earlier.',
    matters: 'Faster feedback can help young companies focus their limited resources.',
    image: 'assets/swipe-founders.jpg',
    imageAlt: 'A small startup team reviewing a product prototype together',
    imagePosition: 'center 35%',
  },
  {
    category: 'Product launches',
    title: 'A new class of devices puts AI within reach',
    deck: 'Companies are exploring products that combine voice, cameras, and on-device assistants.',
    happened: 'Hardware makers are experimenting with more natural ways to access AI features.',
    matters: 'The next useful interface may fit into devices people already carry.',
    image: 'assets/swipe-battery.jpg',
    imageAlt: 'A researcher examining a compact electronic component in a lab',
    imagePosition: 'center 35%',
  },
  {
    category: 'Tech geopolitics',
    title: 'Chip supply chains become a matter of strategy',
    deck: 'Governments are weighing local manufacturing against the cost and complexity of global supply.',
    happened: 'New industrial plans are targeting advanced chip production and key materials.',
    matters: 'Where critical components are made can shape trade and technology policy.',
    image: 'assets/podcast-earth.jpg',
    imageAlt: 'Earth at night with city lights visible across the surface',
    imagePosition: 'center 54%',
  },
  {
    category: 'Tech business',
    title: 'Cooling becomes a key choice for AI infrastructure',
    deck: 'Operators are redesigning server rooms to handle denser computing and rising power needs.',
    happened: 'Data center teams are investing in new cooling systems and layouts.',
    matters: 'Efficient cooling can unlock more computing capacity with less energy.',
    image: 'assets/swipe-data-center.jpg',
    imageAlt: 'Rows of illuminated servers inside a large data center',
    imagePosition: 'center 72%',
  },
  {
    category: 'Technology',
    title: 'Satellite networks reach beyond city coverage',
    deck: 'New launches are adding capacity to services designed for remote areas and moving users.',
    happened: 'Operators continue to build out satellite systems for broader connectivity.',
    matters: 'Reliable links could bring essential services to places traditional networks miss.',
    image: 'assets/swipe-rocket.jpg',
    imageAlt: 'A rocket lifting off above its launch tower at sunset',
    imagePosition: 'center 42%',
  },
  {
    category: 'Product launches',
    title: 'Battery makers target longer days between charges',
    deck: 'Researchers are testing materials and designs that could improve capacity and charging speed.',
    happened: 'Battery labs are working toward cells that store more energy in less space.',
    matters: 'Better batteries can make portable devices and electric transport more practical.',
    image: 'assets/swipe-battery.jpg',
    imageAlt: 'A battery researcher testing an electronic cell in the laboratory',
    imagePosition: 'center 70%',
  },
  {
    category: 'Founders & startups',
    title: 'New tools shorten the path from idea to launch',
    deck: 'Founders can build early versions quickly and see how people respond before scaling up.',
    happened: 'Prototyping tools are making it easier to try product ideas with small teams.',
    matters: 'More experiments help startups learn what customers value sooner.',
    image: 'assets/swipe-founders.jpg',
    imageAlt: 'Founders collaborating around an early product prototype',
    imagePosition: 'center 70%',
  },
];

const imageStories = [
  {
    category: 'Business',
    title: 'Starship takes flight as reusable rocket ambitions grow',
    badges: [{ id: 'most-viewed', label: 'Most viewed' }, { id: 'new', label: 'New' }],
    deck: 'The launch puts attention on rapid turnaround, recovery, and the next phase of space travel.',
    matters: 'Reliable reuse could lower the cost and increase the pace of future launches.',
    image: 'assets/swipe-rocket.jpg',
    alt: 'A tall rocket launching from a coastal pad at sunset',
  },
  {
    category: 'AI',
    title: 'AI’s appetite for compute reshapes the data center',
    deck: 'A new generation of infrastructure is being built to keep up with increasingly powerful models.',
    matters: 'Power and capacity now shape who can build and run advanced AI.',
    image: 'assets/swipe-data-center.jpg',
    alt: 'A technician walking between rows of illuminated computer servers',
  },
  {
    category: 'Technology',
    title: 'Humanoid robots move closer to the factory floor',
    deck: 'Manufacturers are testing how machines can work alongside people on repetitive tasks.',
    matters: 'Real-world trials will show where robots can safely add value.',
    image: 'assets/swipe-robotics.jpg',
    alt: 'A humanoid robot working with people in a manufacturing plant',
  },
  {
    category: 'Founders',
    title: 'Small teams race to build the next big tools',
    deck: 'Founders are finding faster paths from a working prototype to a product people can use.',
    matters: 'Lower building costs let more ideas reach customers quickly.',
    image: 'assets/swipe-founders.jpg',
    alt: 'A small founding team discussing a hardware prototype at night',
  },
  {
    category: 'Innovation',
    title: 'Battery research targets a longer-lasting cell',
    deck: 'New materials could change how everyday devices and vehicles store energy.',
    matters: 'Better storage could extend device life and make electric transport more practical.',
    image: 'assets/swipe-battery.jpg',
    alt: 'A scientist examining a small battery cell in a laboratory',
  },
  {
    category: 'Business',
    title: 'Satellite links bring launch plans closer to daily life',
    deck: 'Rocket launches are helping build networks designed to connect people beyond city infrastructure.',
    matters: 'More reliable coverage could change how remote communities get online.',
    image: 'assets/swipe-rocket.jpg',
    alt: 'A rocket rising above its launch site at dusk',
  },
  {
    category: 'AI',
    title: 'Cooling becomes a key design choice for AI data centers',
    deck: 'Operators are reworking server rooms to manage the heat from denser computing systems.',
    matters: 'Efficient cooling can free up capacity while reducing energy use.',
    image: 'assets/swipe-data-center.jpg',
    alt: 'A technician walking between rows of illuminated computer servers',
  },
  {
    category: 'Technology',
    title: 'Factory robots take on more routine work',
    deck: 'Manufacturers are moving robotics trials from controlled demos into everyday operations.',
    matters: 'Reliable performance on ordinary shifts will determine whether adoption grows.',
    image: 'assets/swipe-robotics.jpg',
    alt: 'A robot working in a modern manufacturing plant',
  },
  {
    category: 'Founders',
    title: 'AI tools help small companies test ideas sooner',
    deck: 'Lean teams are using new software to turn early concepts into working product trials.',
    matters: 'Faster experiments can help founders learn before spending heavily.',
    image: 'assets/swipe-founders.jpg',
    alt: 'A small founding team reviewing an early product prototype',
  },
  {
    category: 'Innovation',
    title: 'Portable power gets a redesign for longer days',
    deck: 'Battery makers are looking for gains in capacity, charging speed, and everyday durability.',
    matters: 'Better portable storage could make new devices more practical to carry.',
    image: 'assets/swipe-battery.jpg',
    alt: 'A researcher examining a battery cell in a laboratory',
  },
];

const glanceStories = [
  {
    category: 'Tech business',
    title: 'The chip race moves beyond the processor',
    badges: [{ id: 'most-glanced', label: 'Most glanced' }],
    deck: 'Memory, power, and cooling are becoming just as important to AI infrastructure.',
    matters: 'The next performance gains may come from the whole system, not one chip.',
  },
  {
    category: 'AI',
    title: 'Agents find a place in everyday work',
    badges: [{ id: 'ai', label: 'AI' }, { id: 'most-read', label: 'Most read' }],
    deck: 'Teams are testing where software can handle a complete task, not just a prompt.',
    matters: 'Useful automation depends on reliable handoffs and clear human control.',
  },
  {
    category: 'Founders & startups',
    title: 'Smaller teams are shipping faster',
    deck: 'New tools shorten the distance between an idea and a product people can try.',
    matters: 'More founders can test demand before committing large resources.',
  },
  {
    category: 'Product launches',
    title: 'A new wave of devices puts AI on the go',
    deck: 'Companies are exploring interfaces built around voice, cameras, and context.',
    matters: 'Portable AI could change when and where people use assistants.',
  },
  {
    category: 'Tech geopolitics',
    title: 'Countries redraw the map for advanced chips',
    deck: 'Manufacturing capacity and supply chains remain central to technology policy.',
    matters: 'Where chips are made affects access, cost, and national resilience.',
  },
  { category: 'Technology', title: 'The browser becomes a workspace for agents', deck: 'Browsers are adding tools for AI to research, organize and act alongside everyday work.', matters: 'The browser may become the place where an agent completes a task.' },
  { category: 'Technology', title: 'The interface after the chat window', deck: 'Voice, screens and background actions are expanding how people direct software.', matters: 'People may move between speaking, looking, and approving as work unfolds.' },
  { category: 'Technology', title: 'Search starts to answer the next question', deck: 'Answer engines are moving from matching queries to anticipating useful follow-ups.', matters: 'Finding information could take fewer searches and less manual sorting.' },
  { category: 'Technology', title: 'Private data becomes useful context', deck: 'Personal context can make assistants more useful when access stays clear and controlled.', matters: 'Trust will depend on people knowing what data an assistant can use.' },
  { category: 'Technology', title: 'Clear controls make complex tools easier to trust', deck: 'Visible permissions help people understand what an agent can access and do.', matters: 'Clear limits make it easier to hand software a real task.' },
];

const articleDetails = [
  [
    'An agent has to do more than produce a good reply. It must keep track of a goal, move between tools, notice when a step fails, and show the person what it plans to do next. The most promising designs make those actions visible rather than hiding them inside a chat window.',
    'That changes the way software is judged. A useful assistant can save time on routine steps, but it also needs clear limits and a simple way to hand a decision back to its user.',
  ],
  [
    'Advanced models need vast amounts of computing, and that demand reaches far beyond the chips themselves. Power connections, memory, networking, cooling, and the buildings that hold them all have to grow together. A delay in any one part can slow the whole system.',
    'For companies trying to offer AI at scale, the physical footprint of computing is becoming part of the product. Capacity planning now shapes cost, speed, and who can serve customers reliably.',
  ],
  [
    'A factory is a harder environment than a staged demonstration. Tasks change, people move nearby, and a machine has to repeat useful work across an entire shift. That is why trials focus on practical jobs and how safely a robot can recover when something goes wrong.',
    'Human teams remain central to those tests. The question is where robots can take strain out of repetitive work while fitting into the pace and safety rules of a real workplace.',
  ],
  [
    'Small teams can now build a working version of an idea before investing in a large launch. Design tools, shared software services, and AI assistance reduce the time spent on the first draft. Founders can put a product in front of people while the idea is still flexible.',
    'Speed alone is not the goal. The value comes from hearing what customers actually need, changing course early, and spending scarce resources on the part that proves useful.',
  ],
  [
    'The next wave of AI hardware is testing whether an assistant can be useful without asking people to open a familiar app. Voice, cameras, and contextual cues can make help feel immediate, but they also create new questions about battery life, privacy, and control.',
    'A successful device will need a clear reason to exist alongside the phone. Its interface must make the useful action easier while keeping the person aware of what it sees and does.',
  ],
  [
    'The path from a chip design to a finished product crosses many borders. Factories, specialist equipment, materials, packaging, and skilled workers are spread across different regions. Governments are trying to reduce weak points without losing the benefits of that global network.',
    'Building local capacity takes time and money. Decisions made now could influence where future computing systems are produced and how readily companies can obtain their most important parts.',
  ],
  [
    'More powerful servers place more heat into a smaller space. Operators can add machines only if the building can deliver power and remove that heat consistently. Cooling choices therefore affect both the size of an AI cluster and the expense of running it.',
    'The work is less visible than a new model announcement, but it has a direct effect on what services can be offered. Better infrastructure gives software teams room to grow.',
  ],
  [
    'Satellite networks aim to fill gaps left by ground infrastructure. Reaching a remote home, a moving vehicle, or a community far from a city depends on more than a launch: the system needs enough capacity, dependable equipment, and a service people can afford.',
    'Each added spacecraft is one part of a larger network. The promise is broader access to communication where laying cables or building towers is difficult.',
  ],
  [
    'Longer battery life depends on a series of tradeoffs. Researchers are looking at materials that hold more energy, charge efficiently, and remain safe through repeated use. A gain in one measure matters only if a cell can be manufactured and relied on at scale.',
    'For people using portable devices, the benefit is simple: more time between interruptions. For makers of electric transport, better storage can change weight, range, and cost.',
  ],
  [
    'Founders can assemble an early product with a smaller team than before, then put it in front of potential users. That does not remove the hard work of choosing a problem, but it lets teams test an assumption before they build an entire business around it.',
    'The best early launches are conversations with customers. Each trial shows what people use, what they ignore, and which part of an idea deserves more work.',
  ],
  [
    'Reusable launch systems are being judged by what happens after liftoff as much as by the flight itself. Recovery, inspection, and preparation for the next mission determine whether a vehicle can fly often enough to change the economics of access to space.',
    'A successful test is a step, not the finish line. The next measure is whether those milestones can be repeated safely and with less time between launches.',
  ],
  [
    'AI services depend on a chain of physical systems that must work together. Faster processors raise demand for memory, network links, power, and cooling. Building one part without the others can leave expensive capacity underused.',
    'This is why infrastructure has moved into the center of the AI story. The pace of new products increasingly depends on whether operators can make enough reliable computing available.',
  ],
  [
    'A humanoid robot may fit spaces designed for people, but that shape alone does not make it useful. Manufacturers are testing whether such machines can perform repetitive jobs safely, handle variation, and keep working when a task does not go exactly as planned.',
    'Practical trials give a clearer answer than a polished demonstration. Workers and operators need to know where a robot helps and where a person remains the better choice.',
  ],
  [
    'The first version of a product no longer has to be the result of a large team and a long build cycle. Founders can combine ready-made services with a focused prototype, then learn from the people who try it.',
    'That faster path increases the number of ideas that can be tested. It also makes clarity more valuable: a small team still needs to know exactly which problem it is solving.',
  ],
  [
    'A longer-lasting cell needs to balance capacity with safety, charging speed, and the ability to survive many cycles. Laboratory progress can point the way, but scaling a material into an affordable product is a separate challenge.',
    'The payoff reaches beyond one device. Better storage can affect everyday electronics, transport, and the systems that use renewable power.',
  ],
  [
    'Space launches increasingly support services used on the ground. A satellite network needs vehicles to place equipment in orbit, then enough coverage and capacity to make that equipment useful to customers.',
    'The practical test is connection quality. For people outside strong terrestrial networks, a dependable link can make work, education, and emergency communication easier to reach.',
  ],
  [
    'Dense computing equipment can strain the systems around it. As operators pack more capability into each rack, they have to rethink airflow, liquid cooling, and how quickly a building can move heat away.',
    'Those decisions shape both cost and capacity. A better cooling design can allow more work from the same space while using energy more carefully.',
  ],
  [
    'Moving from a robotics pilot to a normal shift is a test of consistency. A machine must handle routine variation, make its actions understandable to nearby workers, and recover safely from mistakes.',
    'Manufacturers will keep the jobs that produce a clear benefit. The strongest uses may be narrow, repetitive tasks rather than a single robot that attempts to do everything.',
  ],
  [
    'AI tools can help a small company sketch an interface, write an early version, and gather feedback without waiting for a large development cycle. That shortens the path to the first useful question: will anyone choose to use it?',
    'Quick tests are valuable only when teams learn from them. Founders still need to listen closely, revise the product, and decide when an idea is ready for a larger commitment.',
  ],
  [
    'Portable power is a design problem as well as a materials problem. A useful battery has to fit the product, tolerate daily use, and charge at a speed that works for its owner.',
    'Small gains in several measures can add up to a better experience. The work could give future devices more freedom without asking people to carry more weight.',
  ],
  [
    'The processor remains important, but it is only one part of an AI system. Models also need fast access to memory, dependable power, and cooling that keeps equipment operating under load.',
    'That broadens the competition. Teams that design the whole system well may gain more than teams that improve a chip in isolation.',
  ],
  [
    'The most useful workplace agent may begin with an ordinary task: collect information, update a document, and ask for approval before sending a result. Completing the chain requires the software to understand where human judgment belongs.',
    'Teams are testing these boundaries in everyday work. The aim is to remove repetitive steps while making each handoff clear enough to trust.',
  ],
  [
    'New building tools allow a small team to move from an idea to a trial product quickly. That opens the door to more experiments, including ideas that once would have been too expensive to test.',
    'The advantage is strongest when founders use the extra speed to talk with customers. Shipping early helps only if the next version reflects what they learned.',
  ],
  [
    'Device makers are trying to make AI available at the moment it is needed. Voice and cameras can bring context to an assistant, but the interface must be understandable and easy to interrupt.',
    'Battery life and privacy will shape whether these products become daily tools. A novel form matters less than a clear benefit in a real setting.',
  ],
  [
    'Advanced chip supply chains rely on many specialized steps, often in different countries. New manufacturing plans aim to add capacity and reduce exposure to a disruption in any one place.',
    'Factories alone are not enough. Equipment, materials, skilled workers, and reliable trade routes must grow alongside them for production to be resilient.',
  ],
  [
    'A browser already holds much of a person’s daily work: research, forms, documents, and communication. Agent tools could connect those steps in one place, provided they make their actions visible.',
    'The central design challenge is control. People need to know what an agent has read, what it is about to change, and when it needs permission to continue.',
  ],
  [
    'A chat box is useful for asking a question, but many tasks unfold across voice, screens, and actions in the background. New interfaces are exploring how a person can move between those modes without losing context.',
    'The result should feel easier to direct, not harder to understand. Clear feedback matters when software is doing work beyond the visible conversation.',
  ],
  [
    'Search is moving toward an exchange rather than a single list of links. A useful answer can surface the next question, show where information came from, and help a person decide what to explore further.',
    'That saves effort only when the answer is trustworthy. People still need a clear path back to the sources and a way to check what the system may have missed.',
  ],
  [
    'An assistant becomes more useful when it understands a person’s documents, plans, and preferences. That context is also sensitive, so access has to be deliberate and easy to review.',
    'Good controls should make it obvious what data is available for a task and how to withdraw that access. Useful personalization depends on that trust.',
  ],
  [
    'As software gains the ability to act, its controls become part of the experience. A person should be able to see permissions, check a proposed action, and stop the process without searching through settings.',
    'Those small moments of clarity make a larger difference. People are more willing to delegate work when the boundaries remain visible.',
  ],
];

const glanceVisuals = {
  'Technology': [
    'assets/swipe-robotics.jpg', 'assets/swipe-battery.jpg', 'assets/swipe-data-center.jpg',
  ],
  'AI': ['assets/swipe-data-center.jpg', 'assets/swipe-robotics.jpg'],
  'Tech business': [
    'assets/swipe-data-center.jpg', 'assets/swipe-rocket.jpg', 'assets/swipe-battery.jpg',
  ],
  'Founders & startups': ['assets/swipe-founders.jpg', 'assets/swipe-robotics.jpg'],
  'Product launches': [
    'assets/swipe-battery.jpg', 'assets/swipe-robotics.jpg', 'assets/swipe-founders.jpg',
  ],
  'Tech geopolitics': ['assets/swipe-rocket.jpg', 'assets/swipe-data-center.jpg'],
};

const escapeStoryText = (value) => String(value).replace(/[&<>"']/g, (character) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
})[character]);

// Badges come from the pipeline (feed item.badges: [{id, label}]); the samples below carry a few by hand.
const badgeIcons = {
  exclusive: '<svg viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path d="m8 1 2.1 4.6 5 .6-3.7 3.4 1 5L8 12.1 3.6 14.6l1-5L.9 6.2l5-.6z"/></svg>',
  ai: '<svg viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path d="M6 1.5 7.3 5 11 6.3 7.3 7.6 6 11.2 4.7 7.6 1 6.3 4.7 5zM12 8.5l.8 2 2 .8-2 .8-.8 2-.8-2-2-.8 2-.8z"/></svg>',
  new: '<svg viewBox="0 0 16 16" aria-hidden="true" focusable="false"><circle cx="8" cy="8" r="4"/></svg>',
  'most-viewed': '<svg viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path d="M8.6 1c.3 2.2-.6 3.3-1.8 4.6C5.700 6.900 4.500 8.100 4.500 10a3.500 3.500 0 0 0 7 0c0-1.500-.6-2.500-1.400-3.400-.2.900-.7 1.400-1.300 1.600.5-2.300.2-4.700-.2-7.200z"/></svg>',
  'most-read': '<svg viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path d="M2 2.500h4.500A1.500 1.500 0 0 1 8 4v9.500a1.500 1.500 0 0 0-1.500-1.500H2zm12 0H9.500A1.500 1.500 0 0 0 8 4v9.500a1.500 1.500 0 0 1 1.500-1.500H14z"/></svg>',
  'most-glanced': '<svg viewBox="0 0 16 16" aria-hidden="true" focusable="false"><path d="M8 3C4.500 3 2 6.100 1 8c1 1.900 3.500 5 7 5s6-3.100 7-5c-1-1.900-3.500-5-7-5zm0 8a3 3 0 1 1 0-6 3 3 0 0 1 0 6zm0-1.500a1.500 1.500 0 1 0 0-3 1.500 1.500 0 0 0 0 3z"/></svg>',
};
const renderBadges = (badges) => (badges && badges.length)
  ? `<span class="badges">${badges.map((badge) => `<span class="badge badge-${escapeStoryText(badge.id)}">${badgeIcons[badge.id] || ''}${escapeStoryText(badge.label)}</span>`).join('')}</span>`
  : '';
const categoryClass = (category) => `cat-${String(category).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')}`;

const microphoneIcon = '<svg viewBox="0 0 32 32" aria-hidden="true" focusable="false"><rect x="12" y="4" width="8" height="16" rx="4"/><path d="M8 15a8 8 0 0 0 16 0M16 23v5M11 28h10"/></svg>';

function renderSpotlightPlacement(number) {
  return `
    <figure class="spotlight-placement" id="spotlight-${number}" aria-label="Bought Spotlight placement">
      <figcaption class="spotlight-label">Bought Spotlight <span class="spotlight-dot" aria-hidden="true"></span></figcaption>
      <img src="assets/bought-spotlight-placement.webp" alt="A presenter on screen with the quote: Your design system is productivity theatre." loading="lazy">
    </figure>`;
}

// When the content pipeline's feed is available (see index.html loader), its prime stories replace the samples.
if (window.liveFeed && window.liveFeed.prime && window.liveFeed.prime.length) {
  sampleStories.splice(0, sampleStories.length, ...window.liveFeed.prime.map((item) => ({
    category: item.category,
    title: item.headline,
    deck: item.summary,
    image: item.image_url,
    imageAlt: '',
    imagePosition: 'center 42%',
    video: item.video_url || '',
    poster: item.poster_url || '',
    badges: item.badges || [],
    id: item.id,
    audio: item.audio_url || '',
    source: item.source,
    link: item.link,
  })));
}

function renderStory(story, number, saveKey = number) {
  const loading = number === 1 ? 'eager' : 'lazy';
  return `
    <article class="lead-story ${categoryClass(story.category)}" id="story-${number}" data-story-id="${escapeStoryText(story.id || '')}" aria-labelledby="story-title-${number}" data-story-number="${number}" data-save-key="${saveKey}">
      <div class="video-poster${story.video ? ' has-video' : ''}">
        ${story.video
          ? `<video class="hero-image" src="${escapeStoryText(story.video)}" ${story.poster ? `poster="${escapeStoryText(story.poster)}" preload="none"` : 'preload="metadata"'} playsinline disablepictureinpicture disableremoteplayback aria-label="AI journalist presenting: ${escapeStoryText(story.title)}"></video>`
          : `<img class="hero-image" src="${story.image}" alt="${escapeStoryText(story.imageAlt)}" style="object-position: ${escapeStoryText(story.imagePosition)}" loading="${loading}">`}
        <span class="video-story-number" aria-label="Story ${number} of 50">${number} / 50</span>
        ${story.video ? `<button class="play-news" type="button" aria-label="Play the news: ${escapeStoryText(story.title)}">
          <span class="microphone-circle">${microphoneIcon}<b class="countdown-num" aria-hidden="true"></b><svg class="stop-icon" viewBox="0 0 24 24" aria-hidden="true" focusable="false"><rect x="6" y="6" width="12" height="12" rx="2" /></svg><svg class="countdown-ring" viewBox="0 0 70 70" aria-hidden="true" focusable="false"><circle cx="35" cy="35" r="32" /></svg></span>
          <span class="countdown-label" aria-live="polite"></span>
        </button>
        <button class="pin-close" type="button" aria-label="Close the player"><svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M6 6l12 12M18 6 6 18"/></svg></button>
        <span class="seek-flash" aria-hidden="true"></span>
        <span class="video-progress" aria-hidden="true"><i></i></span>` : `<button class="play-news" type="button" aria-label="Play AI journalist news preview">
          <span class="microphone-circle">${microphoneIcon}</span>
        </button>
        <div class="journalist-window">
          <img src="assets/ai-presenter.jpg" alt="AI journalist presenting the story" loading="${loading}">
        </div>`}
      </div>

      <div class="story-copy">
        <div class="story-meta">
          <span class="story-tags"><span class="story-section">${escapeStoryText(story.category)}</span>${renderBadges(story.badges)}</span>
          <div class="story-actions">
            <button class="story-action" type="button" data-action="save" aria-label="Save story ${number}" aria-pressed="false" title="Save story">
              <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="M6 4.5h12v15l-6-4-6 4z" /></svg>
            </button>
            <button class="story-action" type="button" data-action="share" aria-label="Share story ${number}" title="Share story">
              <svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><circle cx="18" cy="5" r="2" /><circle cx="6" cy="12" r="2" /><circle cx="18" cy="19" r="2" /><path d="m8 11 8-5M8 13l8 5" /></svg>
            </button>
          </div>
        </div>
        <h2 id="story-title-${number}"><button class="story-title-button" type="button" data-open-story="${number}" aria-label="Read full story: ${escapeStoryText(story.title)}">${escapeStoryText(story.title)}</button></h2>
        <p class="story-deck">${escapeStoryText(story.deck)}</p>
        ${story.link
          ? ''
          : `<div class="story-facts">
          <div><h3>What happened</h3><p>${escapeStoryText(story.happened)}</p></div>
          <div><h3>Why it matters</h3><p>${escapeStoryText(story.matters)}</p></div>
        </div>`}
      </div>
    </article>`;
}

function renderImageCarousel() {
  const slides = imageStories.map((story, index) => {
    const number = index + sampleStories.length + 1;
    return `
      <article class="swipe-slide ${categoryClass(story.category)}" id="story-${number}" aria-labelledby="swipe-title-${number}" aria-hidden="${index !== 0}" ${index !== 0 ? 'inert' : ''}>
        <img class="swipe-image" src="${story.image}" alt="${escapeStoryText(story.alt)}" loading="lazy" draggable="false">
        <span class="swipe-story-number" aria-label="Story ${number} of 50">${number} / 50</span>
        <div class="swipe-copy">
          <span class="swipe-tags"><span class="swipe-category">${escapeStoryText(story.category)}</span>${renderBadges(story.badges)}</span>
          <h2 id="swipe-title-${number}"><button class="story-title-button" type="button" data-open-story="${number}" aria-label="Read full story: ${escapeStoryText(story.title)}">${escapeStoryText(story.title)}</button></h2>
          <div class="swipe-facts">
            <div><h3>What happened</h3><p>${escapeStoryText(story.deck)}</p></div>
            <div><h3>Why it matters</h3><p>${escapeStoryText(story.matters)}</p></div>
          </div>
        </div>
      </article>`;
  }).join('');

  const progress = imageStories.map((_, index) => `
    <button class="swipe-progress-step" type="button" aria-label="Show image story ${index + 1} of ${imageStories.length}" aria-current="${index === 0}" data-slide="${index}"></button>`).join('');

  return `
    <section class="image-swipe-block" aria-label="Image news stories">
      <div class="section-break" aria-hidden="true"><span></span><span></span><span></span></div>
      <header class="section-marker"><h2 data-i18n="sec.swipe">Swipe cards</h2></header>
      <div class="image-swipe-card" tabindex="0" aria-roledescription="carousel" aria-label="Image news stories. Swipe or tap the sides to change stories.">
        <div class="swipe-track">${slides}</div>
        <div class="swipe-progress" aria-label="Image story navigation">${progress}</div>
      </div>
      <span class="sr-only swipe-announcement" role="status" aria-live="polite">Image story 1 of ${imageStories.length}</span>
    </section>`;
}

function renderGlances() {
  const visualCounts = {};
  const items = glanceStories.map((story, index) => {
    const number = sampleStories.length + imageStories.length + index + 1;
    const visualSet = glanceVisuals[story.category] || glanceVisuals.Technology;
    const visualIndex = visualCounts[story.category] || 0;
    visualCounts[story.category] = visualIndex + 1;
    const image = visualSet[visualIndex % visualSet.length];
    const imageSide = index % 2 === 0 ? 'start' : 'end';
    const item = `
      <article class="glance-item ${categoryClass(story.category)}${story.deck ? '' : ' is-brief'} is-image-${imageSide}" id="story-${number}" aria-labelledby="glance-title-${number}">
        <div class="glance-visual" aria-hidden="true"><img src="${image}" alt="" loading="${index < 4 ? 'eager' : 'lazy'}"></div>
        <div class="glance-copy">
          <div class="glance-meta"><span class="glance-tags"><span class="glance-category">${escapeStoryText(story.category)}</span>${renderBadges(story.badges)}</span><span class="glance-number" aria-label="Story ${number} of 50">${number} / 50</span></div>
          <h3 id="glance-title-${number}"><button class="story-title-button" type="button" data-open-story="${number}" aria-label="Read full story: ${escapeStoryText(story.title)}">${escapeStoryText(story.title)}</button></h3>
        </div>
        <div class="glance-facts">
          <div><h4>What happened</h4><p>${escapeStoryText(story.deck)}</p></div>
          <div><h4>Why it matters</h4><p>${escapeStoryText(story.matters)}</p></div>
        </div>
      </article>`;
    return item + (index === 4 ? renderSpotlightPlacement(4) : '');
  }).join('');

  return `<section class="glance-section" aria-labelledby="glance-heading">
    <div class="section-break" aria-hidden="true"><span></span><span></span><span></span></div>
    <header class="section-marker"><h2 id="glance-heading" data-i18n="sec.glance">World at a glance</h2></header>
    ${items}
  </section>`;
}

const storiesRoot = document.querySelector('#edition-stories');
storiesRoot.innerHTML = [
  `<section class="prime-section" aria-labelledby="prime-heading">
    <header class="section-marker prime-marker"><h2 id="prime-heading" data-i18n="sec.prime">The Prime</h2></header>
    ${sampleStories.map((story, index) => renderStory(story, index + 1) + (index === 4 ? renderSpotlightPlacement(1) : index === 9 ? renderSpotlightPlacement(2) : '')).join('')}
  </section>`,
  renderImageCarousel(),
  renderSpotlightPlacement(3),
  renderGlances(),
].join('');

const allStories = [...sampleStories, ...imageStories, ...glanceStories];
const articleOverlay = document.querySelector('#article-overlay');
const articleOverlayContent = articleOverlay.querySelector('.article-overlay-content');
let articleOpener = null;

function closeFullStory() {
  if (articleOverlay.hidden) return;
  articleOverlay.hidden = true;
  document.documentElement.classList.remove('is-reading');
  articleOpener?.focus();
  articleOpener = null;
}

let storyTranslations = null;           // {id: {headline, summary}} for the chosen language, or null (English)

function openFullStory(number, opener) {
  const original = allStories[number - 1];
  if (!original) return;
  const tr = storyTranslations && original.id && storyTranslations[original.id];
  const story = tr ? { ...original, title: tr.headline, deck: tr.summary } : original;
  const [opening, continuation] = story.link ? [story.deck, ''] : articleDetails[number - 1] || [story.happened || story.deck, story.matters];
  articleOpener = opener;
  articleOverlayContent.innerHTML = `
    <div class="article-overlay-top">
      <span class="article-overlay-category">${escapeStoryText(story.category)}</span>
      <span class="article-overlay-number">${number} / 50</span>
      <button class="article-overlay-close" type="button" aria-label="Close full story">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 5l14 14M19 5 5 19"/></svg>
      </button>
    </div>
    <article aria-labelledby="article-overlay-title">
      <h2 id="article-overlay-title">${escapeStoryText(story.title)}</h2>
      <p class="article-overlay-deck">${escapeStoryText(story.deck)}</p>
      <div class="article-overlay-rule" aria-hidden="true"></div>
      <div class="article-overlay-body">
        <p>${escapeStoryText(opening)}</p>
        ${story.link
          ? `<p><a href="${escapeStoryText(story.link)}" rel="noopener" target="_blank">Read the full story at ${escapeStoryText(story.source)}</a></p>`
          : `<p>${escapeStoryText(continuation)}</p>
        <h3>Why it matters</h3>
        <p>${escapeStoryText(story.matters)}</p>`}
      </div>
    </article>`;
  articleOverlay.hidden = false;
  articleOverlay.scrollTop = 0;
  document.documentElement.classList.add('is-reading');
  articleOverlay.querySelector('.article-overlay-close').focus();
}

storiesRoot.addEventListener('click', (event) => {
  const title = event.target.closest('[data-open-story]');
  if (title && !(title.closest('.image-swipe-card') && Date.now() < ignoreTapUntil)) {
    openFullStory(Number(title.dataset.openStory), title);
  }
});
articleOverlay.addEventListener('click', (event) => {
  if (event.target.closest('.article-overlay-close')) closeFullStory();
});
document.addEventListener('keydown', (event) => {
  if (articleOverlay.hidden) return;
  if (event.key === 'Escape') closeFullStory();
  if (event.key === 'Tab') {
    event.preventDefault();
    articleOverlay.querySelector('.article-overlay-close').focus();
  }
});

const stickyMasthead = document.querySelector('.sticky-masthead');
function syncMastheadHeight() {
  document.documentElement.style.setProperty('--masthead-height', `${stickyMasthead.getBoundingClientRect().height}px`);
}
syncMastheadHeight();
if ('ResizeObserver' in window) new ResizeObserver(syncMastheadHeight).observe(stickyMasthead);
window.addEventListener('resize', syncMastheadHeight);

const swipeCard = storiesRoot.querySelector('.image-swipe-card');
const swipeTrack = swipeCard.querySelector('.swipe-track');
const swipeSlides = [...swipeCard.querySelectorAll('.swipe-slide')];
const swipeSteps = [...swipeCard.querySelectorAll('.swipe-progress-step')];
const swipeAnnouncement = storiesRoot.querySelector('.swipe-announcement');
let activeImageStory = 0;

function updateImageStory(index) {
  const next = Math.max(0, Math.min(index, swipeSlides.length - 1));
  if (next === activeImageStory) return;
  activeImageStory = next;
  swipeSlides.forEach((slide, slideIndex) => {
    slide.setAttribute('aria-hidden', String(slideIndex !== next));
    slide.inert = slideIndex !== next;
  });
  swipeSteps.forEach((step, stepIndex) => step.setAttribute('aria-current', String(stepIndex === next)));
  swipeAnnouncement.textContent = `Image story ${next + 1} of ${swipeSlides.length}. Story ${next + sampleStories.length + 1} of 50. ${imageStories[next].title}`;
  if (swipeSlides[next + 1]) swipeSlides[next + 1].querySelector('img').loading = 'eager';
}

function showImageStory(index) {
  const next = Math.max(0, Math.min(index, swipeSlides.length - 1));
  swipeTrack.scrollTo({ left: next * swipeTrack.clientWidth, behavior: 'auto' });
  updateImageStory(next);
}

if (swipeSlides[1]) swipeSlides[1].querySelector('img').loading = 'eager';

let scrollFrame = 0;
swipeTrack.addEventListener('scroll', () => {
  if (scrollFrame) return;
  scrollFrame = requestAnimationFrame(() => {
    scrollFrame = 0;
    updateImageStory(Math.round(swipeTrack.scrollLeft / swipeTrack.clientWidth));
  });
}, { passive: true });

swipeTrack.addEventListener('dragstart', (event) => event.preventDefault());

let touchStart = null;
let ignoreTapUntil = 0;
swipeTrack.addEventListener('touchstart', (event) => {
  if (event.touches.length !== 1) return;
  touchStart = { x: event.touches[0].clientX, y: event.touches[0].clientY };
}, { passive: true });
swipeTrack.addEventListener('touchend', (event) => {
  if (!touchStart) return;
  const moved = Math.max(Math.abs(event.changedTouches[0].clientX - touchStart.x), Math.abs(event.changedTouches[0].clientY - touchStart.y));
  if (moved > 8) ignoreTapUntil = Date.now() + 500;
  touchStart = null;
}, { passive: true });

let mouseDrag = null;
swipeTrack.addEventListener('pointerdown', (event) => {
  if (event.pointerType === 'touch' || event.button !== 0) return;
  mouseDrag = { id: event.pointerId, x: event.clientX, left: swipeTrack.scrollLeft, index: activeImageStory, moved: false };
});
window.addEventListener('pointermove', (event) => {
  if (!mouseDrag || event.pointerId !== mouseDrag.id) return;
  const distance = event.clientX - mouseDrag.x;
  if (Math.abs(distance) < 4 && !mouseDrag.moved) return;
  mouseDrag.moved = true;
  swipeTrack.style.scrollSnapType = 'none';
  swipeTrack.scrollLeft = mouseDrag.left - distance;
  if (event.cancelable) event.preventDefault();
});
window.addEventListener('pointerup', (event) => {
  if (!mouseDrag || event.pointerId !== mouseDrag.id) return;
  const drag = mouseDrag;
  mouseDrag = null;
  if (!drag.moved) return;
  swipeTrack.style.scrollSnapType = '';
  ignoreTapUntil = Date.now() + 500;
  const distance = event.clientX - drag.x;
  showImageStory(drag.index + (Math.abs(distance) >= 18 ? (distance < 0 ? 1 : -1) : 0));
});
window.addEventListener('pointercancel', (event) => {
  if (!mouseDrag || event.pointerId !== mouseDrag.id) return;
  const index = mouseDrag.index;
  mouseDrag = null;
  swipeTrack.style.scrollSnapType = '';
  showImageStory(index);
});

swipeCard.addEventListener('click', (event) => {
  if (Date.now() < ignoreTapUntil) return;
  const step = event.target.closest('[data-slide]');
  if (step) {
    showImageStory(Number(step.dataset.slide));
    return;
  }
  if (event.target.closest('[data-open-story]')) return;
  if (!event.target.closest('.swipe-track')) return;
  const bounds = swipeCard.getBoundingClientRect();
  const tapX = (event.clientX - bounds.left) / bounds.width;
  if (tapX < 0.26) showImageStory(activeImageStory - 1);
  else if (tapX > 0.74) showImageStory(activeImageStory + 1);
});

swipeCard.addEventListener('keydown', (event) => {
  if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
  event.preventDefault();
  showImageStory(activeImageStory + (event.key === 'ArrowRight' ? 1 : -1));
});

const savedStorageKey = 'bought-spotlight-saved-2026-10-13';
let savedStories = new Set();
try {
  const stored = JSON.parse(localStorage.getItem(savedStorageKey) || '[]');
  if (Array.isArray(stored)) savedStories = new Set(stored.map(String));
} catch (_) {
  // Saving still works for this visit if browser storage is unavailable.
}

function updateSaveButton(button, storyNumber, saveKey) {
  const isSaved = savedStories.has(saveKey);
  button.setAttribute('aria-pressed', String(isSaved));
  button.setAttribute('aria-label', `${isSaved ? 'Remove saved' : 'Save'} story ${storyNumber}`);
  button.title = isSaved ? 'Remove saved story' : 'Save story';
}

storiesRoot.querySelectorAll('[data-action="save"]').forEach((button) => {
  const article = button.closest('.lead-story');
  updateSaveButton(button, article.dataset.storyNumber, article.dataset.saveKey);
});

const actionFeedback = document.querySelector('#action-feedback');
let feedbackTimeout;
function showActionFeedback(message) {
  actionFeedback.hidden = false;
  actionFeedback.textContent = message;
  clearTimeout(feedbackTimeout);
  feedbackTimeout = setTimeout(() => { actionFeedback.hidden = true; }, 2200);
}

async function copyStoryText(text) {
  if (navigator.clipboard?.writeText) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch (_) {
      // Use the selection fallback below.
    }
  }

  const field = document.createElement('textarea');
  field.value = text;
  field.setAttribute('readonly', '');
  field.style.position = 'fixed';
  field.style.opacity = '0';
  document.body.appendChild(field);
  field.select();
  let copied = false;
  try { copied = document.execCommand('copy'); } catch (_) { /* Copy may be blocked. */ }
  field.remove();
  return copied;
}

async function shareStory(article) {
  const title = article.querySelector('h2').textContent;
  const summary = article.querySelector('.story-deck').textContent;
  const shareData = { title: `${title} — Bought. Spotlight`, text: summary };
  if (location.protocol === 'https:' || location.protocol === 'http:') {
    const url = new URL(location.href);
    url.hash = article.id;
    shareData.url = url.href;
  }

  if (typeof navigator.share === 'function') {
    try {
      await navigator.share(shareData);
      return;
    } catch (error) {
      if (error.name === 'AbortError') return;
    }
  }

  const copy = [title, summary, shareData.url].filter(Boolean).join('\n\n');
  showActionFeedback(await copyStoryText(copy) ? 'Story copied' : 'Could not share story');
}

storiesRoot.addEventListener('click', (event) => {
  const button = event.target.closest('[data-action]');
  if (!button) return;
  const article = button.closest('.lead-story');
  const storyNumber = article.dataset.storyNumber;
  const saveKey = article.dataset.saveKey;

  if (button.dataset.action === 'save') {
    if (savedStories.has(saveKey)) savedStories.delete(saveKey);
    else savedStories.add(saveKey);
    updateSaveButton(button, storyNumber, saveKey);
    try { localStorage.setItem(savedStorageKey, JSON.stringify([...savedStories])); } catch (_) { /* In-memory state remains. */ }
    showActionFeedback(savedStories.has(saveKey) ? 'Story saved' : 'Removed from saved');
  } else if (button.dataset.action === 'share') {
    shareStory(article);
  }
});

// ---- Prime videos: no media controller. Mic button in the middle plays/pauses, the left and right thirds jump 5 s,
// and when a video ends the mic button counts down 3 s, then the page scrolls to the next news video and plays it.
// Tapping the button during the countdown stops the auto-advance.
(() => {
  const SEEK = 5, COUNTDOWN_MS = 3000;
  const posters = () => [...storiesRoot.querySelectorAll('.video-poster.has-video')];
  let countdown = null;                                   // { poster, timer, tick }

  function cancelCountdown() {
    if (!countdown) return;
    clearTimeout(countdown.timer);
    clearInterval(countdown.tick);
    countdown.poster.classList.remove('is-counting');
    countdown.poster.querySelector('.countdown-label').textContent = '';
    countdown = null;
  }

  function flash(poster, text, side) {
    const el = poster.querySelector('.seek-flash');
    el.textContent = text;
    el.dataset.side = side;
    el.classList.remove('is-on');
    void el.offsetWidth;                                  // restart the fade
    el.classList.add('is-on');
  }

  // ---- A playing video that scrolls out of view pins itself under the top bar and keeps playing.
  let pinned = null;                                        // { poster, slot } while a video rides along at the top
  const wide = window.matchMedia('(min-width: 900px)');
  const mastheadHeight = () => document.querySelector('.sticky-masthead').getBoundingClientRect().height;

  function pin(poster) {
    if (pinned) return;
    const box = poster.getBoundingClientRect();
    const slot = document.createElement('div');             // keeps the card's height so nothing below jumps
    slot.className = 'video-slot';
    slot.style.height = `${box.height}px`;
    poster.before(slot);
    if (!wide.matches) { poster.style.left = `${box.left}px`; poster.style.width = `${box.width}px`; }
    poster.classList.add('is-pinned');
    pinned = { poster, slot };
  }

  function unpin() {
    if (!pinned) return;
    pinned.poster.classList.remove('is-pinned');
    pinned.poster.style.left = pinned.poster.style.width = '';
    pinned.slot.remove();
    pinned = null;
  }

  function checkPin() {
    if (pinned) {                                           // back in view: put it in its place again
      if (pinned.slot.getBoundingClientRect().top > mastheadHeight() + 4) unpin();
      return;
    }
    const playing = storiesRoot.querySelector('.video-poster.has-video.is-playing');
    if (playing && playing.getBoundingClientRect().bottom < mastheadHeight() + 24) pin(playing);
  }
  let pinFrame = 0;
  window.addEventListener('scroll', () => {
    if (!pinFrame) pinFrame = requestAnimationFrame(() => { pinFrame = 0; checkPin(); });
  }, { passive: true });
  window.addEventListener('resize', unpin);

  storiesRoot.addEventListener('click', (event) => {
    const close = event.target.closest('.pin-close');
    if (!close) return;
    event.stopPropagation();
    const poster = close.closest('.video-poster');
    poster.querySelector('video').pause();
    cancelCountdown();
    unpin();
  }, true);

  function playPoster(poster) {
    const video = poster.querySelector('video');
    posters().forEach((other) => { if (other !== poster) other.querySelector('video').pause(); });
    if (pinned && pinned.poster !== poster) unpin();        // the next video takes over: the old one goes home
    cancelCountdown();
    if (video.ended) video.currentTime = 0;
    return video.play().catch(() => { /* blocked by the browser: the mic button stays for a tap */ });
  }

  storiesRoot.addEventListener('click', (event) => {
    const poster = event.target.closest('.video-poster.has-video');
    if (!poster) return;
    const video = poster.querySelector('video');
    if (poster.classList.contains('is-counting')) {            // only a tap inside the circle stops the auto-advance
      if (event.target.closest('.microphone-circle')) cancelCountdown();
      return;
    }
    const box = poster.getBoundingClientRect();
    const x = (event.clientX - box.left) / box.width;
    const onButton = event.target.closest('.play-news');
    if (!onButton && x < 0.3) {
      video.currentTime = Math.max(0, video.currentTime - SEEK);
      flash(poster, `−${SEEK}s`, 'back');
    } else if (!onButton && x > 0.7) {
      video.currentTime = Math.min(video.duration || Infinity, video.currentTime + SEEK);
      flash(poster, `+${SEEK}s`, 'fwd');
    } else if (video.paused || video.ended) {
      playPoster(poster);
    } else {
      video.pause();
    }
  });

  storiesRoot.addEventListener('keydown', (event) => {
    const button = event.target.closest('.play-news');
    const poster = button && button.closest('.video-poster.has-video');
    if (!poster || !['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
    const video = poster.querySelector('video');
    const delta = event.key === 'ArrowLeft' ? -SEEK : SEEK;
    video.currentTime = Math.max(0, Math.min(video.duration || Infinity, video.currentTime + delta));
    flash(poster, `${delta < 0 ? '−' : '+'}${SEEK}s`, delta < 0 ? 'back' : 'fwd');
    event.preventDefault();
  });

  // Media events do not bubble, so listen on each video.
  posters().forEach((poster) => {
    const video = poster.querySelector('video');
    const bar = poster.querySelector('.video-progress i');
    video.addEventListener('play', () => poster.classList.add('is-playing'));
    video.addEventListener('pause', () => {
      poster.classList.remove('is-playing');
      if (pinned && pinned.poster === poster && !video.ended) unpin();      // paused: back to its place (ended keeps the countdown on top)
    });
    video.addEventListener('timeupdate', () => { bar.style.width = `${video.duration ? (video.currentTime / video.duration) * 100 : 0}%`; });
    video.addEventListener('ended', () => {
      poster.classList.remove('is-playing');
      bar.style.width = '100%';
      const all = posters();
      const next = all[all.indexOf(poster) + 1];
      if (!next) return;                                  // last video: stay on it with the mic button to replay
      const num = poster.querySelector('.countdown-num');
      const label = poster.querySelector('.countdown-label');
      let left = COUNTDOWN_MS / 1000;
      const show = () => { num.textContent = left; label.textContent = `Next story in ${left}s · tap the circle to stay`; };
      show();
      poster.classList.add('is-counting');
      next.querySelector('video').preload = 'auto';          // only now start fetching the next video, so it is ready at zero
      countdown = {
        poster,
        tick: setInterval(() => { left = Math.max(1, left - 1); show(); }, 1000),
        timer: setTimeout(() => {
          cancelCountdown();
          next.scrollIntoView({ behavior: 'smooth', block: 'center' });
          playPoster(next);
        }, COUNTDOWN_MS),
      };
    });
  });
})();

// ---- Language: the picker (language.js) announces a choice; feed stories swap to their translation (or back to English).
async function applyStoryLanguage(locale, name = '', announce = false) {
  storyTranslations = await window.loadTranslations(locale);
  if (announce && locale !== 'en' && !storyTranslations) showActionFeedback(`Stories are not translated into ${name} yet. Showing English.`);
  storiesRoot.querySelectorAll('.lead-story[data-story-id]').forEach((article) => {
    const tr = storyTranslations && storyTranslations[article.dataset.storyId];
    const title = article.querySelector('.story-title-button');
    const deck = article.querySelector('.story-deck');
    title.dataset.en = title.dataset.en || title.textContent;
    if (deck) deck.dataset.en = deck.dataset.en || deck.textContent;
    const headline = tr ? tr.headline : title.dataset.en;
    title.textContent = headline;
    title.setAttribute('aria-label', `Read full story: ${headline}`);
    if (deck) deck.textContent = tr ? tr.summary : deck.dataset.en;
  });
  if (!articleOverlay.hidden) closeFullStory();
}
document.addEventListener('bought:language', (event) => applyStoryLanguage(event.detail.locale, event.detail.name, true));
window.applyUiText();
if (window.boughtLanguage && window.boughtLanguage.locale !== 'en') applyStoryLanguage(window.boughtLanguage.locale);
