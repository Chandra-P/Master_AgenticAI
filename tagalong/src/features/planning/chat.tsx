'use client';

import {avatarTextColor} from '@/lib/avatar-contrast';
import {useEffect, useRef, useState, type KeyboardEvent} from 'react';
import Link from 'next/link';
import {ArrowLeft, AtSign, Check, LayoutDashboard, Send, Sparkles} from 'lucide-react';
import type {Plan, Tab} from '@/services/types';
import {Button} from '@/components/ui/button';
import {usePlanning} from './store';
import {fictionalCast} from '@/services/demo-plan';
import {FindOptionsButton} from './research/option-workbench';
import {TypingSuggestions} from './typing-suggestions';
import {useTypingSuggestions} from './use-typing-suggestions';

export function Chat({plan, onTab}: {plan: Plan; onTab: (tab: Tab) => void}) {
  const {sendMessage, mode, user, config, workspaceRole} = usePlanning();
  const [text, setText] = useState('');
  const [thinking, setThinking] = useState(false);
  const [suggestionsEnabled, setSuggestionsEnabled] = useState(true);
  const [dismissed, setDismissed] = useState<string | null>(null);
  const [caretAtEnd, setCaretAtEnd] = useState(true);
  const [isComposing, setIsComposing] = useState(false);
  const composing = useRef(false);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const oldCount = useRef(plan.messages.length);
  const conversationRef=useRef<HTMLDivElement>(null);
  const demoStory=plan.demo_template==='austin-four-friends';
  useEffect(()=>{if(demoStory&&conversationRef.current)conversationRef.current.scrollTop=0;},[demoStory,plan.id]);
  const completion = useTypingSuggestions({
    plan, text, enabled: suggestionsEnabled && caretAtEnd && !isComposing && dismissed !== text && !thinking,
    connected: mode === 'connected' && !!user && !!config?.connectedReady,
    config, identity: [mode, user?.id, workspaceRole].join(':'),
  });
  const suggestion = completion.suggestion;

  useEffect(() => {
    if (plan.messages.length > oldCount.current) {
      endRef.current?.scrollIntoView({behavior: 'smooth', block: 'nearest'});
    }
    oldCount.current = plan.messages.length;
  }, [plan.messages.length]);

  function acceptSuggestion() {
    const input = inputRef.current;
    if (!suggestion || !input || composing.current ||
        input.selectionStart !== text.length || input.selectionEnd !== text.length) return;
    const next = text + suggestion;
    setText(next);
    setCaretAtEnd(true);
    input.focus();
    requestAnimationFrame(() => {
      // A later edit, focus change, or plan switch owns the caret now.
      if (inputRef.current !== input || !input.isConnected || input.value !== next ||
          document.activeElement !== input || input.selectionStart !== next.length ||
          input.selectionEnd !== next.length) return;
      input.setSelectionRange(next.length, next.length);
    });
  }

  async function send() {
    const message = text.trim();
    if (!message || thinking || composing.current) return;
    setThinking(true);
    setText('');
    try {
      await sendMessage(plan.id, message);
    } catch {
      // The persistent workspace error banner explains failed sends.
    } finally {
      setThinking(false);
    }
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (composing.current || event.nativeEvent.isComposing || event.nativeEvent.keyCode === 229) return;
    if (event.key === 'Escape' && suggestion) {
      event.preventDefault();
      setDismissed(text);
    }
    if (event.key === 'Tab' && !event.shiftKey && suggestion &&
        event.currentTarget.selectionStart === text.length && event.currentTarget.selectionEnd === text.length) {
      event.preventDefault();
      acceptSuggestion();
    }
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void send();
    }
  }

  return <section className="chat-panel">
    <div className="chat-heading">
      <div>
        <h2>All the good ideas start here.</h2>
        <p><span className="online-dot"/>{demoStory?'4 fictional friends, one weekend':plan.members.length+' people, one great plan'}</p>
      </div>
      <a className="text-button" href={'#plan-ideas-'+plan.id}>Get city ideas and events</a><FindOptionsButton plan={plan}/><span className="chat-demo">{mode === 'demo' ? 'Demo conversation' : 'Group conversation'}</span>
      {mode === 'demo' && <Link className="text-button" href="/account">Use live AI in shared workspace</Link>}
    </div>
    {demoStory&&<div className="demo-conversation-intro"><strong>Four friends planning together</strong><p>Alex, Maya, Sam and Jordan are fictional adults. Follow their ideas, objections and compromises below. Scripted dialogue and votes are separate from real members and the live AI check.</p><div className="journey-buttons"><Button variant="outline" onClick={()=>conversationRef.current?.scrollTo({top:0,behavior:'smooth'})}>Replay from the first idea</Button><Button variant="outline" onClick={()=>onTab('Decisions')}>See their options and votes</Button><Button variant="outline" onClick={()=>onTab('Itinerary')}>See the final itinerary</Button></div></div>}<div className="chat-messages" ref={conversationRef}>
      <div className="chat-date"><span/>THE BEGINNING OF SOMETHING GOOD<span/></div>
      {plan.messages.map(message => {
        const member = plan.members.find(person => message.user_id
          ? person.user_id === message.user_id : person.name === message.author);
        const author = member?.name || message.author;
        const fictional=message.simulation?fictionalCast.find(person=>person.name===message.author):undefined;
        return <article key={message.id} className={'chat-message ' + (message.assistant ? 'assistant-message' : '')}>
          {message.assistant
            ? <span className="avatar ai-avatar"><Sparkles size={18}/></span>
            : <span className="avatar" style={{background: fictional?.color || member?.color || '#eccfc0',color:avatarTextColor(fictional?.color || member?.color || '#eccfc0')}}>{author.slice(0, 1)}</span>}
          <div className="message-content">
            <div className="message-byline">
              <strong>{author}{!message.simulation && message.author === (user?.name || 'Alex') && <em>you</em>}</strong>
              {message.assistant && <span className="simulated-label">{message.simulation?'Scripted demo assistant':mode==='demo'?'Simulated assistant':demoStory?'Live AI reply':'AI suggestion'}</span>}
              {message.simulation&&!message.assistant&&<span className="simulated-label">Fictional friend</span>}<time>{message.time}</time>
            </div>
            <div className="message-bubble">
              {message.text}
              {!!message.sources?.length && <details className="message-sources">
                <summary>Sources ({message.sources.length})</summary>
                {message.sources.map(source => <blockquote key={source.id}>
                  <strong>{source.title}</strong><p>{source.text}</p>
                </blockquote>)}
              </details>}
              {message.assistant && <div className="assistant-actions">
                <button onClick={() => onTab(message.simulation?'Decisions':'Planning board')}>
                  <LayoutDashboard size={13}/> {message.simulation?'See the group decisions':'See the planning board'} <ArrowLeft className="arrow-right" size={13}/>
                </button>
              </div>}
            </div>
          </div>
        </article>;
      })}
      {thinking && <div className="thinking" role="status"><Sparkles size={15}/> Tagalong is putting a few ideas together…</div>}
      <div ref={endRef}/>
    </div>
    <div className="chat-composer-wrap">
      <div className="chat-tip">
        <Sparkles size={14}/>
        <span>A little nudge? Mention <b>@Tagalong</b> {mode === 'demo' ? 'for a simulated helping hand.' : 'for a planning suggestion.'}</span>
        <button type="button" className="text-button" onClick={() => onTab('Demo bookings')}>Try demo restaurant booking</button>
      </div>
      <form className="chat-composer" onSubmit={event => {event.preventDefault(); void send();}}>
        <textarea
          ref={inputRef}
          aria-label="Message your group"
          value={text}
          maxLength={2000}
          onChange={event => {
            const input = event.target;
            setText(input.value);
            setDismissed(null);
            setCaretAtEnd(input.selectionStart === input.value.length && input.selectionEnd === input.value.length);
          }}
          onSelect={event => setCaretAtEnd(event.currentTarget.selectionStart === text.length && event.currentTarget.selectionEnd === text.length)}
          onCompositionStart={() => {composing.current = true; setIsComposing(true);}}
          onCompositionEnd={() => {composing.current = false; setIsComposing(false);}}
          placeholder="Good ideas welcome. What are you thinking?"
          onKeyDown={handleKeyDown}
        />
        <div className="composer-bottom">
          <button type="button" className="mention-button" aria-label="Mention Tagalong" onClick={() => setText(value => value + '@Tagalong ')}>
            <AtSign size={16}/><span>Tagalong</span>
          </button>
          <span className="composer-hint">Enter to send</span>
          <Button type="submit" size="icon" disabled={!text.trim() || thinking} aria-label="Send message"><Send size={17}/></Button>
        </div>
      </form>
      <TypingSuggestions enabled={suggestionsEnabled} onEnabled={setSuggestionsEnabled} suggestion={suggestion} onAccept={acceptSuggestion} model={completion.model} status={completion.status}/>
      <span className="composer-note">
        <Check size={11}/>{mode === 'demo' ? 'Local demo · your messages stay in this browser' : 'Shared with this plan’s members · AI suggestions need review'}
      </span>
    </div>
  </section>;
}
