import { Link } from 'react-router-dom';
import ThemeToggle from '../components/ThemeToggle.tsx';
import { useDocumentTitle } from '../hooks/useDocumentTitle.ts';
import '../styles/not-found-page.css';

export default function NotFoundPage() {
  useDocumentTitle('kort — link not found');

  return (
    <>
      <ThemeToggle />
      <div className="page">
        <main className="content">
          <div className="content-head">
            <div className="brand">kort</div>
            <h1>Link not found</h1>
          </div>

          <p className="not-found-text">
            This short link doesn’t exist or has expired. Links work for 1 year after they’re created.
          </p>

          <Link className="primary-button not-found-action" to="/">
            Shorten a new link
          </Link>
        </main>
      </div>
    </>
  );
}
