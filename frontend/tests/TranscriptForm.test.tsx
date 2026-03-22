import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { TranscriptForm } from '../src/components/TranscriptForm';

vi.mock('../src/api/transcript', () => ({
  downloadTranscript: vi.fn(),
}));

import { downloadTranscript } from '../src/api/transcript';

const mockDownload = downloadTranscript as ReturnType<typeof vi.fn>;

beforeEach(() => {
  mockDownload.mockReset();
});

describe('TranscriptForm', () => {
  it('renders all core controls', () => {
    render(<TranscriptForm />);

    expect(screen.getByLabelText(/youtube urls/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/include timestamps/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/language/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /download transcript/i })).toBeInTheDocument();
  });

  it('shows filename field when exactly one URL is entered, hides it for multiple', async () => {
    const user = userEvent.setup();
    render(<TranscriptForm />);

    const textarea = screen.getByLabelText(/youtube urls/i);

    // No URL — filename field should not be visible
    expect(screen.queryByLabelText(/custom filename/i)).not.toBeInTheDocument();

    // One URL
    await user.type(textarea, 'https://www.youtube.com/watch?v=abc123');
    expect(screen.getByLabelText(/custom filename/i)).toBeInTheDocument();

    // Two URLs — filename field should disappear
    await user.type(textarea, '\nhttps://www.youtube.com/watch?v=def456');
    expect(screen.queryByLabelText(/custom filename/i)).not.toBeInTheDocument();
  });

  it('toggles the timestamps checkbox', async () => {
    const user = userEvent.setup();
    render(<TranscriptForm />);

    const checkbox = screen.getByLabelText(/include timestamps/i) as HTMLInputElement;
    expect(checkbox.checked).toBe(true);

    await user.click(checkbox);
    expect(checkbox.checked).toBe(false);

    await user.click(checkbox);
    expect(checkbox.checked).toBe(true);
  });

  it('calls downloadTranscript with the correct payload on submit', async () => {
    const user = userEvent.setup();
    mockDownload.mockResolvedValue({});
    render(<TranscriptForm />);

    const textarea = screen.getByLabelText(/youtube urls/i);
    await user.type(textarea, 'https://www.youtube.com/watch?v=abc123');

    const filenameInput = screen.getByLabelText(/custom filename/i);
    await user.type(filenameInput, 'my_transcript');

    const languageSelect = screen.getByLabelText(/language/i);
    await user.selectOptions(languageSelect, 'es');

    const checkbox = screen.getByLabelText(/include timestamps/i);
    await user.click(checkbox);

    await user.click(screen.getByRole('button', { name: /download transcript/i }));

    await waitFor(() => {
      expect(mockDownload).toHaveBeenCalledOnce();
      expect(mockDownload).toHaveBeenCalledWith({
        urls: ['https://www.youtube.com/watch?v=abc123'],
        include_timestamps: false,
        language: 'es',
        filename: 'my_transcript',
      });
    });
  });

  it('calls downloadTranscript without filename for multiple URLs', async () => {
    const user = userEvent.setup();
    mockDownload.mockResolvedValue({});
    render(<TranscriptForm />);

    const textarea = screen.getByLabelText(/youtube urls/i);
    await user.type(textarea, 'https://www.youtube.com/watch?v=abc123\nhttps://www.youtube.com/watch?v=def456');

    await user.click(screen.getByRole('button', { name: /download transcript/i }));

    await waitFor(() => {
      expect(mockDownload).toHaveBeenCalledWith({
        urls: [
          'https://www.youtube.com/watch?v=abc123',
          'https://www.youtube.com/watch?v=def456',
        ],
        include_timestamps: true,
        language: 'en',
      });
    });
  });

  it('shows loading spinner and disables controls during an in-flight request', async () => {
    const user = userEvent.setup();
    let resolveDownload!: (value: Record<string, never>) => void;
    mockDownload.mockReturnValue(
      new Promise<Record<string, never>>((resolve) => {
        resolveDownload = resolve;
      })
    );

    render(<TranscriptForm />);

    const textarea = screen.getByLabelText(/youtube urls/i);
    await user.type(textarea, 'https://www.youtube.com/watch?v=abc123');

    const button = screen.getByRole('button', { name: /download transcript/i });
    await user.click(button);

    // Spinner should be present and controls disabled during loading
    expect(screen.getByRole('status', { name: /loading/i })).toBeInTheDocument();
    expect(button).toBeDisabled();
    expect(textarea).toBeDisabled();
    expect(screen.getByLabelText(/include timestamps/i)).toBeDisabled();
    expect(screen.getByLabelText(/language/i)).toBeDisabled();

    resolveDownload({});

    await waitFor(() => {
      expect(screen.queryByRole('status', { name: /loading/i })).not.toBeInTheDocument();
    });
  });

  it('displays an error message when downloadTranscript returns an error', async () => {
    const user = userEvent.setup();
    mockDownload.mockResolvedValue({ error: 'Could not fetch transcript.' });
    render(<TranscriptForm />);

    const textarea = screen.getByLabelText(/youtube urls/i);
    await user.type(textarea, 'https://www.youtube.com/watch?v=bad');

    await user.click(screen.getByRole('button', { name: /download transcript/i }));

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Could not fetch transcript.');
    });
  });

  it('clears the error on a new submit attempt', async () => {
    const user = userEvent.setup();
    mockDownload.mockResolvedValueOnce({ error: 'First error' }).mockResolvedValueOnce({});
    render(<TranscriptForm />);

    const textarea = screen.getByLabelText(/youtube urls/i);
    await user.type(textarea, 'https://www.youtube.com/watch?v=abc123');

    const button = screen.getByRole('button', { name: /download transcript/i });

    await user.click(button);
    await waitFor(() => expect(screen.getByRole('alert')).toBeInTheDocument());

    await user.click(button);

    // Error should be gone while loading (cleared on new submit)
    await waitFor(() => {
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });
});
