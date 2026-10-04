import type {Lang} from './news-data';

type Lens = { kicker: string; title: string; items: { label: string; text: string }[] };

export const longView: Record<Lang, Lens> = {
  en: {
    kicker: 'THE TEN-YEAR LENS',
    title: 'What today changes over time.',
    items: [
      {label: 'CAPACITY', text: 'Power, land and cooling are becoming part of AI strategy.'},
      {label: 'WORK', text: 'Software will be judged by the tasks it reliably completes.'},
      {label: 'TRUST', text: 'Machine identities are becoming a core business control.'},
    ],
  },
  es: {
    kicker: 'LA MIRADA A DIEZ AÑOS',
    title: 'Lo que hoy cambia a largo plazo.',
    items: [
      {label: 'CAPACIDAD', text: 'Energía, terreno y refrigeración ya forman parte de la estrategia de IA.'},
      {label: 'TRABAJO', text: 'El software se medirá por las tareas que termina de forma fiable.'},
      {label: 'CONFIANZA', text: 'Las identidades de máquinas serán un control empresarial esencial.'},
    ],
  },
  hi: {
    kicker: 'दस साल की नज़र',
    title: 'आज के बदलाव का लंबा असर।',
    items: [
      {label: 'क्षमता', text: 'बिजली, ज़मीन और कूलिंग अब एआई रणनीति का हिस्सा बन रहे हैं।'},
      {label: 'काम', text: 'सॉफ़्टवेयर का मूल्यांकन उसके भरोसेमंद ढंग से पूरे किए काम से होगा।'},
      {label: 'भरोसा', text: 'मशीन पहचान कारोबार के नियंत्रण का अहम हिस्सा बन रही है।'},
    ],
  },
};
