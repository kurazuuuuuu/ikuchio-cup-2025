export function generateFingerprint(): string {
  try {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    if (!ctx) {
      throw new Error('Canvas context not available');
    }
    
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillText('Fingerprint test', 2, 2);
    
    const fingerprint = [
      navigator.userAgent || 'unknown',
      navigator.language || 'unknown',
      screen.width + 'x' + screen.height || 'unknown',
      new Date().getTimezoneOffset() || 0,
      canvas.toDataURL()
    ].join('|');
    
    const encoded = btoa(fingerprint).slice(0, 32);
    if (!encoded || encoded.length < 8) {
      throw new Error('Invalid fingerprint generated');
    }
    
    return encoded;
  } catch (error) {
    console.warn('フィンガープリント生成に失敗しました:', error);
    // フォールバック用のランダムID生成
    return 'fallback_' + Math.random().toString(36).substr(2, 16);
  }
}
