import { useEffect, useImperativeHandle, useRef, type Ref } from 'react';

declare global {
  interface Window {
    turnstile?: {
      render: (container: HTMLElement, options: Record<string, unknown>) => string;
      reset: (widgetId: string) => void;
      remove: (widgetId: string) => void;
    };
  }
}

export interface TurnstileHandle {
  reset: () => void;
}

const SCRIPT_SRC = 'https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit';
// Cloudflare's always-pass test key in dev, paired with the backend's dev test secret.
const SITE_KEY = import.meta.env.VITE_TURNSTILE_SITE_KEY || (import.meta.env.DEV ? '1x00000000000000000000AA' : '');

let scriptPromise: Promise<void> | null = null;

function loadScript(): Promise<void> {
  scriptPromise ??= new Promise((resolve, reject) => {
    const script = document.createElement('script');
    script.src = SCRIPT_SRC;
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => {
      scriptPromise = null;
      reject(new Error('Turnstile failed to load'));
    };
    document.head.appendChild(script);
  });
  return scriptPromise;
}

interface Props {
  onToken: (token: string | null) => void;
  onFailed: () => void;
  ref?: Ref<TurnstileHandle>;
}

export default function Turnstile({ onToken, onFailed, ref }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const widgetId = useRef<string | null>(null);
  const onTokenRef = useRef(onToken);
  const onFailedRef = useRef(onFailed);

  useEffect(() => {
    onTokenRef.current = onToken;
    onFailedRef.current = onFailed;
  }, [onToken, onFailed]);

  useImperativeHandle(ref, () => ({
    // Tokens are single-use, so a fresh one is needed after every submit.
    reset() {
      onTokenRef.current(null);
      if (widgetId.current && window.turnstile) window.turnstile.reset(widgetId.current);
    },
  }), []);

  useEffect(() => {
    let cancelled = false;
    loadScript()
      .then(() => {
        if (cancelled || !containerRef.current || !window.turnstile) return;
        widgetId.current = window.turnstile.render(containerRef.current, {
          sitekey: SITE_KEY,
          appearance: 'interaction-only',
          theme: document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light',
          callback: (token: string) => onTokenRef.current(token),
          // Expiry is recoverable on its own; an error-callback or a script
          // that never loads is not, hence the separate signal.
          'expired-callback': () => onTokenRef.current(null),
          'error-callback': () => {
            onTokenRef.current(null);
            onFailedRef.current();
          },
        });
      })
      .catch(() => {
        onTokenRef.current(null);
        onFailedRef.current();
      });

    return () => {
      cancelled = true;
      if (widgetId.current && window.turnstile) window.turnstile.remove(widgetId.current);
      widgetId.current = null;
    };
  }, []);

  return <div ref={containerRef} className="turnstile" />;
}
