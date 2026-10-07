import type { Link } from '../models/Link.ts';

interface RawLink {
  code: string;
  url: string;
  expires_at: string;
}

export class LinkError extends Error {
  status: number;

  constructor(status: number) {
    super(`Link request failed: ${status}`);
    this.status = status;
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

export const LinkRepository = {
  async create(url: string): Promise<Link> {
    const response = await fetch('/api/links/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({ url }),
    });
    if (!response.ok) throw new LinkError(response.status);
    return mapLink(await response.json());
  },
};
