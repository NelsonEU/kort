import { useRef, useState, type FormEvent } from 'react';
import ThemeToggle from '../components/ThemeToggle.tsx';
import { useDocumentTitle } from '../hooks/useDocumentTitle.ts';
import type { Link } from '../models/Link.ts';
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

export default function HomePage() {
  useDocumentTitle('kort — shorten a link');
  const [input, setInput] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [link, setLink] = useState<Link | null>(null);
  const [copied, setCopied] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const shortRef = useRef<HTMLAnchorElement>(null);

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);

    const url = normalizeUrl(input);
    if (!url) {
      setError('That doesn’t look like a valid URL.');
      inputRef.current?.focus();
      return;
    }

    setSubmitting(true);
    try {
      setLink(await LinkRepository.create(url));
      setCopied(false);
    } catch (err) {
      setLink(null);
      setError(
        err instanceof LinkError && err.status === 429
          ? 'You’ve made a lot of links recently. Please try again later.'
          : 'Couldn’t shorten that link. Please try again.'
      );
    } finally {
      setSubmitting(false);
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
            <button className="primary-button home-submit" type="submit" disabled={submitting}>
              {submitting ? 'Shortening…' : 'Shorten'}
            </button>
          </form>

          <p className="home-error" role="alert" hidden={!error}>
            {error}
          </p>

          {/* Always mounted (just hidden) so screen readers announce the
              result: a live region inserted together with its content isn't. */}
          <div className="home-result" aria-live="polite" hidden={!link}>
            {link && (
              <>
                <a ref={shortRef} className="home-short" href={link.shortUrl} target="_blank" rel="noopener">
                  {link.shortUrl.replace(/^https?:\/\//, '')}
                </a>
                <button className="home-copy" type="button" onClick={handleCopy}>
                  {copied ? 'Copied' : 'Copy'}
                </button>
              </>
            )}
          </div>

          <p className="home-note">No account. Every link works for 1 year.</p>
        </main>
      </div>
    </>
  );
}
