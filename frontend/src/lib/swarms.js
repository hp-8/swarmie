// Swarm catalogue — static config for the PitchInput workbench.
// Each swarm answers one founder decision and carries its own input voice
// (title, sub, placeholder, template) plus the checklist patterns used to
// light up the "has section" cues. Pure data: no component state here.

export const SWARMS = [
  {
    key: 'validate',
    label: 'Validate',
    blurb: 'Will the market care?',
    enabled: true,
    agentNoun: 'agents',
    title: 'What are we roasting?',
    sub: '<em>"AI for sales"</em> is too thin. <em>"AI inbox triage for B2B AEs hitting &gt;50 cold replies/day, $49/seat"</em> is a pitch.',
    placeholder: `PROBLEM: What pain are you solving? Who feels it?

PRODUCT: What does your product do? One-liner + key features.

AUDIENCE: Who is this for? Be specific — role, company size, industry.

PRICING: How much? Free tier? Per-seat? Usage-based?

COMPETITORS: Who else solves this? Why are you different?`,
    template: `PROBLEM:\n\nPRODUCT:\n\nAUDIENCE:\n\nPRICING:\n\nCOMPETITORS: `,
    checks: [
      { key: 'problem', label: 'problem', pattern: /problem[:\s].*\S/ },
      { key: 'product', label: 'product', pattern: /product[:\s].*\S/ },
      { key: 'audience', label: 'audience', pattern: /audience[:\s].*\S|target[:\s].*\S|who[:\s].*\S|icp[:\s].*\S/ },
      { key: 'pricing', label: 'pricing', pattern: /pric(e|ing)[:\s].*\S|\$\d/ },
      { key: 'competitor', label: 'competitors', pattern: /competitor[:\s].*\S|vs\.?\s|alternative|compared to/ },
    ],
  },
  {
    key: 'investor',
    label: 'Investor',
    blurb: 'Is it fundable?',
    enabled: true,
    agentNoun: 'investors',
    title: 'What deck are we stress-testing?',
    sub: 'A swarm of investor archetypes reads your deck like inbox #47. You get the likely questions, the missing proof, and the pass reasons before a real partner does.',
    placeholder: `PROBLEM: What pain, and why is it urgent now?

SOLUTION: The product + the wedge. Why you win.

MARKET: How big, and why venture-scale?

TRACTION: Revenue, users, growth, retention — real numbers.

TEAM: Who you are, why you'll win this.

RAISE: Stage + amount + what it buys.`,
    template: `PROBLEM:\n\nSOLUTION:\n\nMARKET:\n\nTRACTION:\n\nTEAM:\n\nRAISE: `,
    checks: [
      { key: 'problem', label: 'problem', pattern: /problem[:\s].*\S/ },
      { key: 'market', label: 'market', pattern: /market[:\s].*\S|tam[:\s].*\S/ },
      { key: 'traction', label: 'traction', pattern: /traction[:\s].*\S|revenue|users|mrr|arr|growth|retention/ },
      { key: 'team', label: 'team', pattern: /team[:\s].*\S|founder[:\s].*\S/ },
      { key: 'raise', label: 'raise', pattern: /rais(e|ing)[:\s].*\S|round[:\s].*\S|pre-?seed|seed|series\s/ },
    ],
  },
  {
    key: 'launch',
    label: 'Launch',
    blurb: 'Will the launch land?',
    enabled: true,
    agentNoun: 'commenters',
    title: 'How will the launch land?',
    sub: 'A swarm of Product Hunt, HN, Reddit, Indie Hackers and X archetypes reacts to your launch. You get the questions, objections, confusion, and risks likely to surface before you go live.',
    placeholder: `PRODUCT: What are you launching? One clear sentence.

AUDIENCE: Who is this for? Be specific.

CHANNEL: Where are you launching? (Product Hunt, HN, Reddit, X, newsletter...)

DIFFERENTIATION: Why is this different from what already exists?

TIMING: Why now? Is there a trend or moment this taps into?`,
    template: `PRODUCT:\n\nAUDIENCE:\n\nCHANNEL:\n\nDIFFERENTIATION:\n\nTIMING: `,
    checks: [
      { key: 'problem', label: 'product', pattern: /product[:\s].*\S/ },
      { key: 'audience', label: 'audience', pattern: /audience[:\s].*\S|target[:\s].*\S|who[:\s].*\S|icp[:\s].*\S/ },
      { key: 'channel', label: 'channel', pattern: /channel[:\s].*\S|product hunt|hacker news|reddit|twitter|x\.com|newsletter|indie hacker/ },
      { key: 'differentiation', label: 'differentiation', pattern: /differenti[:\s].*\S|unique[:\s].*\S|different[:\s].*\S|vs\.?\s|alternative/ },
      { key: 'timing', label: 'timing', pattern: /timing[:\s].*\S|why now[:\s].*\S|trend[:\s].*\S|moment[:\s].*\S/ },
    ],
  },
]
