import { Languages } from 'lucide-react';
import { useTranslation } from 'react-i18next';

const languages = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
  { code: 'zh', name: '中文', flag: '🇨🇳' },
];

export function LanguageSelector() {
  const { i18n, t } = useTranslation();

  const handleLanguageChange = (langCode) => {
    i18n.changeLanguage(langCode);
    localStorage.setItem('preferredLanguage', langCode);
  };

  const currentLanguage = languages.find(lang => lang.code === i18n.language) || languages[0];

  return (
    <div className="relative group">
      <button className="inline-flex items-center gap-2 rounded-xl border px-3 py-1.5 text-sm hover:bg-neutral-50 transition-colors">
        <Languages className="w-4 h-4" />
        <span className="hidden sm:inline">{currentLanguage.flag} {currentLanguage.name}</span>
        <span className="sm:hidden">{currentLanguage.flag}</span>
      </button>
      
      <div className="absolute right-0 top-full mt-1 w-48 bg-white rounded-xl border shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-20">
        <div className="py-1">
          {languages.map((language) => (
            <button
              key={language.code}
              onClick={() => handleLanguageChange(language.code)}
              className={`w-full px-3 py-2 text-left text-sm hover:bg-neutral-50 flex items-center gap-2 ${
                i18n.language === language.code ? 'bg-neutral-100 font-medium' : ''
              }`}
            >
              <span>{language.flag}</span>
              <span>{language.name}</span>
              {i18n.language === language.code && (
                <span className="ml-auto text-neutral-500">✓</span>
              )}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}