.pragma library
// UI texts (pl, en). The language comes from the phone setting (uiLang, main.py).
// A missing entry falls back to English.

var texts = {
    "subtitle":    { "pl": "Kopie układu ikon: %1", "en": "Icon layout backups: %1" },
    "empty":       { "pl": "Brak kopii.\nZapisz układ ikon przyciskiem poniżej.",
                     "en": "No backups yet.\nSave the icon layout with the button below." },
    "readError":   { "pl": "Nie udało się odczytać kopii", "en": "Could not read the backups" },
    "saveNow":     { "pl": "Zapisz układ", "en": "Save layout" },
    "saved":       { "pl": "Zapisano MyDocs/MeeGrid/%1", "en": "Saved MyDocs/MeeGrid/%1" },
    "kind_manual": { "pl": "ręczna", "en": "manual" },
    "kind_auto":   { "pl": "automatyczna", "en": "automatic" },
    "kind_before": { "pl": "przed przywróceniem", "en": "before restore" },
    "counts":      { "pl": "ikony: %1 · foldery: %2", "en": "icons: %1 · folders: %2" },
    "missingN":    { "pl": "brak aplikacji: %1", "en": "apps not installed: %1" },
    "broken":      { "pl": "uszkodzona kopia", "en": "damaged backup" },
    "previewSub":  { "pl": "Podgląd układu z kopii", "en": "Layout preview from the backup" },
    "restore":     { "pl": "Przywróć", "en": "Restore" },
    "restoreQ":    { "pl": "Przywrócić układ z %1?", "en": "Restore the layout from %1?" },
    "restoreInfo": { "pl": "Ekran główny zniknie na kilka sekund i wróci z układem z tej kopii. Obecny układ zostanie najpierw zapisany jako kopia „przed przywróceniem”.",
                     "en": "The home screen disappears for a few seconds and comes back with the layout from this backup. The current layout is saved first as a \"before restore\" backup." },
    "missingInfo": { "pl": "Tych aplikacji nie ma teraz w telefonie: %1. Ekran główny może pominąć ich ikony. Najlepiej najpierw je zainstalować (np. MeeRevive), a potem przywrócić układ.",
                     "en": "These apps are not on the phone now: %1. The home screen may drop their icons. Best install them first (e.g. MeeRevive) and restore the layout afterwards." },
    "restoring":   { "pl": "Przywracanie układu…", "en": "Restoring the layout…" },
    "saving":      { "pl": "Zapisywanie…", "en": "Saving…" },
    "restored":    { "pl": "Układ przywrócony", "en": "Layout restored" },
    "failed":      { "pl": "Nie udało się: %1", "en": "Failed: %1" },
    "noAnswer":    { "pl": "Usługa MeeGrid nie odpowiada. Uruchom telefon ponownie i spróbuj jeszcze raz.",
                     "en": "The MeeGrid service does not answer. Restart the phone and try again." },
    "errNoService":{ "pl": "Usługa MeeGrid nie działa (startuje kilka minut po włączeniu telefonu).",
                     "en": "The MeeGrid service is not running (it starts a few minutes after the phone boots)." },
    "errBroken":   { "pl": "kopia jest uszkodzona", "en": "the backup is damaged" },
    "errNoStage":  { "pl": "brak przygotowanej kopii", "en": "no prepared backup" },
    "delete":      { "pl": "Usuń", "en": "Delete" },
    "deleteQ":     { "pl": "Usunąć kopię z %1?", "en": "Delete the backup from %1?" },
    "settings":    { "pl": "Ustawienia", "en": "Settings" },
    "autoTitle":   { "pl": "Kopia automatyczna", "en": "Automatic backup" },
    "howOften":    { "pl": "Jak często", "en": "How often" },
    "daily":       { "pl": "codziennie", "en": "every day" },
    "weekly":      { "pl": "raz w tygodniu", "en": "once a week" },
    "atHour":      { "pl": "O godzinie", "en": "At" },
    "keepTitle":   { "pl": "Ile kopii automatycznych trzymać", "en": "Automatic backups to keep" },
    "keepN":       { "pl": "%1 ostatnich", "en": "last %1" },
    "lastAuto":    { "pl": "Ostatnia kopia automatyczna: %1", "en": "Last automatic backup: %1" },
    "nextAuto":    { "pl": "Następna: %1", "en": "Next: %1" },
    "skipNext":    { "pl": "Pomiń najbliższą kopię", "en": "Skip the next backup" },
    "unskip":      { "pl": "Cofnij pominięcie", "en": "Undo skip" },
    "skippedLine": { "pl": "Pominięta: %1", "en": "Skipped: %1" },
    "skippedBanner":{ "pl": "Kopia z %1 zostanie pominięta. Następna: %2", "en": "The backup of %1 will be skipped. Next: %2" },
    "unskippedBanner":{ "pl": "Następna kopia: %1", "en": "Next backup: %1" },
    "autoOnBanner":{ "pl": "Kopia automatyczna włączona. Pierwsza: %1", "en": "Automatic backup on. First one: %1" },
    "offQ":        { "pl": "Wyłączyć kopię automatyczną?", "en": "Turn off the automatic backup?" },
    "offText":     { "pl": "Nowe kopie automatyczne przestaną powstawać. Zapisane kopie zostają w MyDocs/MeeGrid i nic nie zostanie usunięte. Możesz ją w każdej chwili włączyć z powrotem.",
                     "en": "No new automatic backups will be made. Saved backups stay in MyDocs/MeeGrid and nothing is deleted. You can switch it back on at any time." },
    "turnOff":     { "pl": "Wyłącz", "en": "Turn off" },
    "change":      { "pl": "Zmień", "en": "Change" },
    "keepLowerText":{ "pl": "Przy następnej kopii automatycznej zostanie usuniętych %1 najstarszych kopii automatycznych, żeby zostało %2. Kopie ręczne nie są ruszane.",
                     "en": "At the next automatic backup the %1 oldest automatic backups will be deleted, so that %2 remain. Manual backups are not touched." },
    "statusOff":   { "pl": "Kopia automatyczna wyłączona", "en": "Automatic backup off" },
    "statusOn":    { "pl": "Automatycznie %1 o %2 · następna %3", "en": "Automatic %1 at %2 · next %3" },
    "never":       { "pl": "jeszcze nie było", "en": "none yet" },
    "autoOffInfo": { "pl": "Wyłączona. Kopie zapisujesz tylko przyciskiem „Zapisz układ”.",
                     "en": "Off. Backups are made only with the \"Save layout\" button." },
    "autoInfo":    { "pl": "Kopia powstaje tylko wtedy, gdy układ ikon zmienił się od ostatniej kopii; bez zmian nic nie jest zapisywane. Jeśli telefon był wyłączony o tej godzinie, kopia powstanie kilkanaście minut po włączeniu. Gdy kopii automatycznych jest więcej, niż ustawiono, najstarsza jest usuwana. Kopie ręczne nigdy nie są usuwane automatycznie; kopii „przed przywróceniem” trzymamy 5 ostatnich.",
                     "en": "A backup is made only when the icon layout changed since the last backup; without changes nothing is saved. If the phone was off at that hour, the backup is made some 15 minutes after it is switched on. When there are more automatic backups than set, the oldest one is deleted. Manual backups are never deleted automatically; the last 5 \"before restore\" backups are kept." },
    "toPc":        { "pl": "Kopia na komputer", "en": "Copy to a computer" },
    "toPcText":    { "pl": "Kopie są w MyDocs/MeeGrid (pliki .tar.gz). Pełne flashowanie z obrazem eMMC kasuje MyDocs, więc przed flashowaniem skopiuj ten folder na komputer (kabel USB w trybie pamięci masowej albo scp), a po flashowaniu wgraj go z powrotem.",
                     "en": "Backups are in MyDocs/MeeGrid (.tar.gz files). A full flash with the eMMC image erases MyDocs, so copy this folder to a computer before flashing (USB mass storage or scp) and put it back afterwards." },
    "about":       { "pl": "O programie", "en": "About" },
    "aboutText":   { "pl": "Kopia i przywracanie układu ikon ekranu głównego: pozycje ikon, foldery i pasek szybkiego uruchamiania. Przydaje się po flashowaniu albo gdy układ się pomiesza.",
                     "en": "Backup and restore of the home screen icon layout: icon positions, folders and the quick launch bar. Useful after flashing or when the layout gets scrambled." },
    "credit":      { "pl": "Zaprojektowany i napisany przez Claude (Anthropic) wspólnie ze smyhu dla Nokii N9.",
                     "en": "Designed and written by Claude (Anthropic) together with smyhu for the Nokia N9." },
    "version":     { "pl": "Wersja %1", "en": "Version %1" },
    "close":       { "pl": "Zamknij", "en": "Close" },
    "cancel":      { "pl": "Anuluj", "en": "Cancel" },
    "folders":     { "pl": "Foldery: %1", "en": "Folders: %1" },
    "fromHost":    { "pl": "Telefon: %1", "en": "Phone: %1" }
};

function t(lang, key) {
    var e = texts[key];
    if (!e)
        return key;
    return e[lang] !== undefined ? e[lang] : (e["en"] !== undefined ? e["en"] : key);
}

function a(lang, key, arg) {
    return t(lang, key).replace("%1", arg);
}

function a2(lang, key, arg1, arg2) {
    return t(lang, key).replace("%1", arg1).replace("%2", arg2);
}

// error keys from the backend are translated, other texts are shown as they are
function err(lang, e) {
    if (("" + e).indexOf("errRead") == 0)
        return e;
    return texts[e] ? t(lang, e) : e;
}
