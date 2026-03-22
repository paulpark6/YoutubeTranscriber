import { useState } from 'react';
import { downloadTranscript } from '../api/transcript';
import { LanguageSelector } from './LanguageSelector';
import { ErrorMessage } from './ErrorMessage';
import { LoadingSpinner } from './LoadingSpinner';

function getNonEmptyLines(text: string): string[] {
  return text.split('\n').filter((line) => line.trim().length > 0);
}

export function TranscriptForm() {
  const [urlsText, setUrlsText] = useState('');
  const [filename, setFilename] = useState('');
  const [includeTimestamps, setIncludeTimestamps] = useState(true);
  const [language, setLanguage] = useState('en');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | string[] | null>(null);

  const urls = getNonEmptyLines(urlsText);
  const isSingleUrl = urls.length === 1;

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const result = await downloadTranscript({
      urls,
      include_timestamps: includeTimestamps,
      language,
      ...(isSingleUrl && filename.trim() ? { filename: filename.trim() } : {}),
    });

    setLoading(false);

    if (result.error !== undefined) {
      setError(result.error);
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      <div>
        <label htmlFor="urls" style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 600 }}>
          YouTube URLs
        </label>
        <textarea
          id="urls"
          value={urlsText}
          onChange={(e) => setUrlsText(e.target.value)}
          placeholder="Paste YouTube URLs here, one per line"
          disabled={loading}
          rows={6}
          style={{ width: '100%', boxSizing: 'border-box', resize: 'vertical' }}
        />
      </div>

      {isSingleUrl && (
        <div>
          <label
            htmlFor="filename"
            style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 600 }}
          >
            Custom filename (optional)
          </label>
          <input
            id="filename"
            type="text"
            value={filename}
            onChange={(e) => setFilename(e.target.value)}
            placeholder="my_transcript"
            disabled={loading}
            style={{ width: '100%', boxSizing: 'border-box' }}
          />
        </div>
      )}

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <input
          id="timestamps"
          type="checkbox"
          checked={includeTimestamps}
          onChange={(e) => setIncludeTimestamps(e.target.checked)}
          disabled={loading}
        />
        <label htmlFor="timestamps">Include timestamps</label>
      </div>

      <div>
        <label
          htmlFor="language"
          style={{ display: 'block', marginBottom: '0.25rem', fontWeight: 600 }}
        >
          Language
        </label>
        <LanguageSelector value={language} onChange={setLanguage} disabled={loading} />
      </div>

      <div>
        <button
          type="submit"
          disabled={loading || urls.length === 0}
          style={{ padding: '0.5rem 1.25rem', cursor: loading ? 'not-allowed' : 'pointer' }}
        >
          {loading && <LoadingSpinner />}
          Download Transcript
        </button>
      </div>

      {error !== null && <ErrorMessage error={error} />}
    </form>
  );
}
