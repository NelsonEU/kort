import type { ExpiresIn, Link } from '../models/Link.ts';

interface RawLink {
  code: string;
  url: string;
  expires_at: string | null;
}

export class LinkError extends Error {
  status: number;
  code: string | null;

  constructor(status: number, code: string | null) {
    super(`Link request failed: ${status}${code ? ` (${code})` : ''}`);
    this.status = status;
    this.code = code;
  }
}

function mapLink(raw: RawLink): Link {
  return {
    code: raw.code,
    url: raw.url,
    shortUrl: `${window.location.origin}/${raw.code}`,
    expiresAt: raw.expires_at,
  };
}

async function readErrorCode(response: Response): Promise<string | null> {
  try {
    const body = await response.json();
    return typeof body?.error === 'string' ? body.error : null;
  } catch {
    return null;
  }
}

export const LinkRepository = {
  async create(url: string, expiresIn: ExpiresIn, turnstileToken: string): Promise<Link> {
    const response = await fetch('/api/links/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ url, expires_in: expiresIn, turnstile_token: turnstileToken }),
    });
    if (!response.ok) throw new LinkError(response.status, await readErrorCode(response));
    return mapLink(await response.json());
  },
};
