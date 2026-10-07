import { useCallback, useRef, useState, type FormEvent } from 'react';
import ThemeToggle from '../components/ThemeToggle.tsx';
import Turnstile, { type TurnstileHandle } from '../components/Turnstile.tsx';
import { useDocumentTitle } from '../hooks/useDocumentTitle.ts';
import { EXPIRY_OPTIONS, type ExpiresIn, type Link } from '../models/Link.ts';
import { LinkError, LinkRepository } from '../repositories/LinkRepository.ts';
import '../styles/home-page.css';

function normalizeUrl(value: string): string | null {
  let v = value.trim();
  if (!v) return null;
  if (!/^[a-z][a-z0-9+.-]*:\/\//i.test(v)) v = 'https://' + v;
  try {
    const u = new URL(v);
    if (u.protocol !== 'http:' && u.protocol !== 'https:') return null;
    if (!u.hostname.includes('.')) return null;
    return u.href;
  } catch {
    return null;
  }
}

function errorMessage(err: unknown): string {
  if (err instanceof LinkError) {
    if (err.status === 429) return 'You’ve made a lot of links recently. Please try again later.';
    switch (err.code) {
      case 'unsafe_url':
        return 'Google Safe Browsing flags this link as unsafe, so it can’t be shortened.';
      case 'blocked_domain':
        return 'Links to other shorteners, IP addresses or kort itself can’t be shortened.';
      case 'captcha_failed':
        return 'We couldn’t verify that you’re human. Please try again.';
      case 'safety_check_unavailable':
        return 'We couldn’t check that link for safety right now. Please try again in a moment.';
    }
  }
  return 'Couldn’t shorten that link. Please try again.';
}

function formatExpiry(expiresAt: string | null): string {
  if (!expiresAt) return 'Never expires';
  const date = new Date(expiresAt).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' });
  return `Works until ${date}`;
}

export default function HomePage() {
  useDocumentTitle('kort — shorten a link');
  const [input, setInput] = useState('');
  const [expiresIn, setExpiresIn] = useState<ExpiresIn | null>(null);
  const [turnstileToken, setTurnstileToken] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [link, setLink] = useState<Link | null>(null);
  const [copied, setCopied] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const shortRef = useRef<HTMLAnchorElement>(null);
  const turnstileRef = useRef<TurnstileHandle>(null);
  const handleToken = useCallback((token: string | null) => setTurnstileToken(token), []);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);

    const url = normalizeUrl(input);
    if (!url) {
      setError('That doesn’t look like a valid URL.');
      inputRef.current?.focus();
      return;
    }
    if (!expiresIn) {
      setError('Choose how long the link should work.');
      return;
    }
    if (!turnstileToken) {
      setError('Still checking that you’re human. Try again in a moment.');
      return;
    }

    setSubmitting(true);
    try {
      setLink(await LinkRepository.create(url, expiresIn, turnstileToken));
      setCopied(false);
    } catch (err) {
      setLink(null);
      setError(errorMessage(err));
    } finally {
      setSubmitting(false);
      turnstileRef.current?.reset();
    }
  }

  async function handleCopy() {
    if (!link) return;
    try {
      await navigator.clipboard.writeText(link.shortUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      const selection = window.getSelection();
      if (!selection || !shortRef.current) return;
      const range = document.createRange();
      range.selectNodeContents(shortRef.current);
      selection.removeAllRanges();
      selection.addRange(range);
    }
  }

  return (
    <>
      <ThemeToggle />
      <div className="page">
        <main className="content">
          <div className="content-head">
            <div className="brand">kort</div>
            <h1>Shorten a link</h1>
          </div>

          <form className="home-form" onSubmit={handleSubmit} noValidate>
            <label className="sr-only" htmlFor="url">
              Long URL
            </label>
            <input
              ref={inputRef}
              id="url"
              className="home-input"
              name="url"
              type="url"
              inputMode="url"
              autoComplete="off"
              autoFocus
              required
              placeholder="Paste a long URL"
              value={input}
              onChange={(e) => setInput(e.target.value)}
            />

            <div className="home-expiry" role="radiogroup" aria-label="Link works for">
              {EXPIRY_OPTIONS.map((option) => (
                <label key={option.value} className="home-expiry-option">
                  <input
                    type="radio"
                    name="expires_in"
                    value={option.value}
                    checked={expiresIn === option.value}
                    onChange={() => setExpiresIn(option.value)}
                  />
                  <span>{option.label}</span>
                </label>
              ))}
            </div>

            <button className="primary-button home-submit" type="submit" disabled={submitting}>
              {submitting ? 'Shortening…' : 'Shorten'}
            </button>

            <p className="home-error" role="alert">
              <span hidden={!error}>{error}</span>
            </p>

            <Turnstile ref={turnstileRef} onToken={handleToken} />
          </form>

          {/* Always mounted (just hidden) so screen readers announce the
              result: a live region inserted together with its content isn't. */}
          <div className="home-result" aria-live="polite" hidden={!link}>
            {link && (
              <>
                <div className="home-result-main">
                  <a ref={shortRef} className="home-short" href={link.shortUrl} target="_blank" rel="noopener">
                    {link.shortUrl.replace(/^https?:\/\//, '')}
                  </a>
                  <span className="home-expires">{formatExpiry(link.expiresAt)}</span>
                </div>
                <button className="home-copy" type="button" onClick={handleCopy}>
                  {copied ? 'Copied' : 'Copy'}
                </button>
              </>
            )}
          </div>

          <p className="home-note">No account. Pick how long your link works, up to a year.</p>
        </main>
      </div>
    </>
  );
}
