'use client';

import {useEffect, useState} from 'react';
import {ConnectedService, getAuth, type PublicConfig} from '@/services/connected';
import {suggestContinuation} from '@/services/typing-suggestions';
import type {Plan} from '@/services/types';

interface Options {
  plan: Plan;
  text: string;
  enabled: boolean;
  connected: boolean;
  config: PublicConfig | null;
  identity: string;
}

interface Completion {key: string; suggestion: string; failed: boolean}

/** Only the settled, current draft may supply a model completion. */
export function useTypingSuggestions({plan, text, enabled, connected, config, identity}: Options) {
  const [completion, setCompletion] = useState<Completion | null>(null);
  const eligible = enabled && connected && !!config?.connectedReady &&
    text.trim().length >= 3 && text.length <= 1800 && !/[\u0000-\u001f\u007f]/.test(text) && !!plan.revision;
  const key = JSON.stringify([identity, plan.id, plan.revision, text]);

  useEffect(() => {
    if (!eligible || !config) return;
    let active = true;
    const controller = new AbortController();
    const timer = setTimeout(() => {
      void Promise.resolve().then(() => {
        const service = new ConnectedService(getAuth(config));
        return service.typingSuggestion(plan.id, text, plan.revision!, controller.signal);
      }).then(result => {
        if (!active || controller.signal.aborted) return;
        const suffix = typeof result.suggestion === 'string' ? result.suggestion : '';
        const safe = suffix.length <= Math.min(80, 2000 - text.length) &&
          suffix.trim().split(/\s+/).filter(Boolean).length <= 8 && !/[\u0000-\u001f\u007f]/.test(suffix);
        setCompletion({key, suggestion: safe ? suffix : '', failed: !safe});
      }).catch(() => {
        if (active && !controller.signal.aborted) setCompletion({key, suggestion: '', failed: true});
      });
    }, 750);
    return () => {active = false; clearTimeout(timer); controller.abort();};
  }, [eligible, config, identity, key, plan.id, plan.revision, text]);

  const local = enabled ? suggestContinuation(text, plan) : '';
  const current = eligible && completion?.key === key ? completion : null;
  return {
    suggestion: current?.suggestion || local,
    model: connected,
    status: !enabled ? '' : !connected ? '' : !eligible
      ? 'Pause after at least 3 characters for an OpenAI suggestion.'
      : current?.failed ? 'OpenAI suggestions unavailable. Local suggestions remain available.'
      : current ? current.suggestion ? 'OpenAI suggestion ready.' : 'No OpenAI completion this time. Local suggestions remain available.'
      : 'OpenAI suggests after you pause typing.',
  };
}
