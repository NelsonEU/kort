export type ExpiresIn = '1d' | '1w' | '1m' | '1y';

export const EXPIRY_OPTIONS: { value: ExpiresIn; label: string }[] = [
  { value: '1d', label: '1 day' },
  { value: '1w', label: '1 week' },
  { value: '1m', label: '1 month' },
  { value: '1y', label: '1 year' },
];

export interface Link {
  code: string;
  url: string;
  shortUrl: string;
  expiresAt: string | null;
}
