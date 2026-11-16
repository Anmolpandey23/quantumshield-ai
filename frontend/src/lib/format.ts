/** UTC-based formatting so SSR and browser output always match. */
export const fmtTime = (iso: string) => iso.slice(11, 19);
export const fmtDateTime = (iso: string) => `${iso.slice(5, 10)} ${iso.slice(11, 16)}`;
