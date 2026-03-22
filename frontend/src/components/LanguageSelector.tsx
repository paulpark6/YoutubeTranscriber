interface LanguageSelectorProps {
  value: string;
  onChange: (lang: string) => void;
  disabled?: boolean;
}

const LANGUAGES: { name: string; code: string }[] = [
  { name: 'English', code: 'en' },
  { name: 'Spanish', code: 'es' },
  { name: 'French', code: 'fr' },
  { name: 'German', code: 'de' },
  { name: 'Portuguese', code: 'pt' },
  { name: 'Japanese', code: 'ja' },
  { name: 'Korean', code: 'ko' },
  { name: 'Chinese', code: 'zh' },
  { name: 'Hindi', code: 'hi' },
  { name: 'Arabic', code: 'ar' },
];

export function LanguageSelector({ value, onChange, disabled }: LanguageSelectorProps) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      disabled={disabled}
      aria-label="Language"
    >
      {LANGUAGES.map((lang) => (
        <option key={lang.code} value={lang.code}>
          {lang.name} ({lang.code})
        </option>
      ))}
    </select>
  );
}
