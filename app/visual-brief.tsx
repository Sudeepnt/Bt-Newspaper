"use client";

import {ArrowRight, Check, LockKeyhole, Play} from 'lucide-react';
import {deskName, type DeskId, type Lang, type News} from './news-data';

type Props = {story: News; lang: Lang; compact?: boolean; playing?: boolean};

export function VisualBrief({story, lang, compact=false, playing=false}: Props) {
  return <div className={`signal-visual signal-${story.desk}${compact?' signal-compact':''}${playing?' signal-playing':''}`} aria-hidden="true">
    <div className="signal-head"><span>BOUGHT / {deskName(story.desk, lang)}</span><span>{story.media==='watch'?'MOTION BRIEF':'VISUAL BRIEF'}</span></div>
    <div className="signal-art">
      {story.desk==='business'&&<div className="art-bars"><span/><span/><span/><span/><span/><i>DEMAND</i><b>CAPACITY</b></div>}
      {story.desk==='ai'&&<div className="art-agents"><div><small>01</small><b>ASK</b><ArrowRight/></div><div><small>02</small><b>DO</b><ArrowRight/></div><div><small>03</small><b>VERIFY</b><Check/></div></div>}
      {story.desk==='founders'&&<div className="art-founder"><div className="founder-head"/><div className="founder-body"/><span>BUILD → LISTEN → REBUILD</span></div>}
      {story.desk==='launches'&&<div className="art-product"><div><i/><i/><i/></div><section><b>PRODUCT</b><span/><span/><span/></section><aside><b>LIVE</b><span>↗</span></aside></div>}
      {story.desk==='software'&&<div className="art-flow"><span>INPUT</span><i/><span>WORKFLOW</span><i/><span>DONE</span></div>}
      {story.desk==='chips'&&<div className="art-chip"><div><span/><span/><span/><span/></div><b>COMPUTE</b></div>}
      {story.desk==='capital'&&<div className="art-capital"><span className="cap-figure">$</span><div><i/><i/><i/><i/></div><b>LOOK AT THE TERMS</b></div>}
      {story.desk==='security'&&<div className="art-security"><div><span/><span/><span/><span/><span/><span/></div><LockKeyhole size={58} strokeWidth={1.25}/><b>WHO HAS ACCESS?</b></div>}
    </div>
    <div className="signal-foot"><span><i className="signal-dot"/> {playing?'ON AIR':'THE SIGNAL'}</span><strong>{story.headline[lang]}</strong>{story.media==='watch'&&<Play size={15} fill="currentColor"/>}</div>
  </div>;
}

export function ReporterAvatar({desk, large=false}: {desk: DeskId; large?: boolean}) {
  if (desk==='business') return <span className={`reporter-avatar reporter-photo${large?' reporter-large':''}`}><img src="/mara-vale.png" alt=""/></span>;
  return <span className={`reporter-avatar reporter-${desk}${large?' reporter-large':''}`} aria-hidden="true">
    <i className="reporter-hair"/><i className="reporter-head"/><i className="reporter-neck"/><i className="reporter-body"/><b>AI</b>
  </span>;
}
