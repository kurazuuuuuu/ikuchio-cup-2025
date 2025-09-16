export function generateFingerprint(): string {
  try {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    if (!ctx) {
      throw new Error('Canvas context not available');
    }
    
    // 固定テキストでCanvas描画（デバイス固有の描画特性を取得）
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillText('Device Fingerprint Test', 2, 2);
    
    const fingerprint = [
      navigator.userAgent || 'unknown',
      navigator.hardwareConcurrency || 'unknown',
      (navigator as any).deviceMemory || 'unknown',
      navigator.platform || 'unknown',
      canvas.toDataURL()
    ].join('|');
    
    // ハッシュ生成
    let hash = 0;
    for (let i = 0; i < fingerprint.length; i++) {
      const char = fingerprint.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    
    const encoded = Math.abs(hash).toString(36);
    
    if (!encoded || encoded.length < 8) {
      throw new Error('Invalid fingerprint generated');
    }
    
    return encoded.slice(0, 16);
  } catch (error) {
    console.warn('フィンガープリント生成に失敗しました:', error);
    // フォールバック用の固定ID生成（ランダムではなくブラウザ情報ベース）
    const fallbackData = navigator.userAgent + navigator.platform + (navigator.hardwareConcurrency || '');
    let fallbackHash = 0;
    for (let i = 0; i < fallbackData.length; i++) {
      fallbackHash = ((fallbackHash << 5) - fallbackHash) + fallbackData.charCodeAt(i);
      fallbackHash = fallbackHash & fallbackHash;
    }
    return 'fb_' + Math.abs(fallbackHash).toString(36).slice(0, 12);
  }
}
