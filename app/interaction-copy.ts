import type {Lang} from './news-data';

export const interactionCopy: Record<Lang, {
  share: string; copied: string; copyFailed: string; back: string; next: string; listen: string;
  watchHeading: string; watchDeck: string; picturesHeading: string; picturesDeck: string;
  swipeHint: string; headline: string; what: string; why: string; voice: string; source: string; sample: string;
  newsroom: string; newsroomDeck: string; openDesk: string; visualBrief: string;
}> = {
  en: {
    share:'Share story', copied:'Story link copied', copyFailed:'Copy the link shown below', back:'Back', next:'Next', listen:'Listen',
    watchHeading:'Watch the desks', watchDeck:'Fast visual briefings with a journalist in the frame.', picturesHeading:'Today in pictures', picturesDeck:'The issue through signals, products and diagrams.',
    swipeHint:'Swipe or tap through four cards', headline:'THE HEADLINE', what:'WHAT HAPPENED', why:'WHY IT MATTERS', voice:'THE JOURNALIST’S TAKE', source:'SOURCE TRAIL', sample:'Sample reporting; original links would appear here in a live issue.',
    newsroom:'The newsroom', newsroomDeck:'Eight dedicated AI journalists, each with a beat and a point of view.', openDesk:'Open desk', visualBrief:'Play visual brief',
  },
  es: {
    share:'Compartir noticia', copied:'Enlace copiado', copyFailed:'Copia el enlace que aparece abajo', back:'Atrás', next:'Siguiente', listen:'Escuchar',
    watchHeading:'Ver las secciones', watchDeck:'Resúmenes visuales rápidos con un periodista en pantalla.', picturesHeading:'Hoy en imágenes', picturesDeck:'La edición en señales, productos y diagramas.',
    swipeHint:'Desliza o toca para ver cuatro tarjetas', headline:'EL TITULAR', what:'QUÉ PASÓ', why:'POR QUÉ IMPORTA', voice:'LA MIRADA DEL PERIODISTA', source:'RUTA DE FUENTES', sample:'Noticias de muestra; una edición real enlazaría las fuentes originales.',
    newsroom:'La redacción', newsroomDeck:'Ocho periodistas de IA, cada uno con tema y mirada propios.', openDesk:'Abrir sección', visualBrief:'Ver resumen visual',
  },
  hi: {
    share:'खबर शेयर करें', copied:'खबर का लिंक कॉपी हुआ', copyFailed:'नीचे दिया लिंक कॉपी करें', back:'पीछे', next:'आगे', listen:'सुनें',
    watchHeading:'विभागों को देखें', watchDeck:'पत्रकार के साथ तेज़ दृश्य समाचार सार।', picturesHeading:'आज की तस्वीरें', picturesDeck:'संकेतों, उत्पादों और चित्रों में आज का अंक।',
    swipeHint:'चार कार्ड देखने के लिए स्वाइप या टैप करें', headline:'मुख्य खबर', what:'क्या हुआ', why:'यह क्यों महत्वपूर्ण है', voice:'पत्रकार की नज़र', source:'स्रोत की जानकारी', sample:'ये नमूना खबरें हैं; असली अंक में मूल स्रोत के लिंक होंगे।',
    newsroom:'न्यूज़रूम', newsroomDeck:'आठ एआई पत्रकार, हर एक का अपना विषय और नज़रिया।', openDesk:'विभाग खोलें', visualBrief:'दृश्य सार चलाएँ',
  },
};
