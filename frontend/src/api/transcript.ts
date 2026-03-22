export interface TranscriptRequest {
  urls: string[];
  include_timestamps: boolean;
  language: string;
  filename?: string;
}

export async function downloadTranscript(
  params: TranscriptRequest
): Promise<{ error?: string | string[] }> {
  const baseUrl = '';

  let response: Response;
  try {
    response = await fetch(`${baseUrl}/api/transcript`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(params),
    });
  } catch {
    return { error: 'Network error: could not reach the server.' };
  }

  if (!response.ok) {
    try {
      const body = (await response.json()) as { detail?: string | string[] };
      const detail = body.detail;
      if (typeof detail === 'string' || Array.isArray(detail)) {
        return { error: detail };
      }
      return { error: `Request failed with status ${response.status}.` };
    } catch {
      return { error: `Request failed with status ${response.status}.` };
    }
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);

  const disposition = response.headers.get('Content-Disposition') ?? '';
  const filenameMatch = disposition.match(/filename="?([^"]+)"?/);
  const downloadName = filenameMatch?.[1] ?? 'transcript';

  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = downloadName;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);

  return {};
}
