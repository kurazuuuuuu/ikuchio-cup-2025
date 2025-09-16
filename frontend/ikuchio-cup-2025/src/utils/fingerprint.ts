export function generateFingerprint(): string {
  try {
    // ランダム要素を追加して一意性を高める
    const randomSeed = Math.random().toString(36) + Date.now().toString(36);
    
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    if (!ctx) {
      throw new Error('Canvas context not available');
    }
    
    // ランダムなテキストでCanvas描画
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillText('FP_' + randomSeed.slice(0, 10), 2, 2);
    
    const fingerprint = [
      navigator.userAgent || 'unknown',
      navigator.language || 'unknown',
      navigator.languages?.join(',') || 'unknown',
      screen.width + 'x' + screen.height + 'x' + screen.colorDepth || 'unknown',
      new Date().getTimezoneOffset() || 0,
      navigator.hardwareConcurrency || 'unknown',
      navigator.deviceMemory || 'unknown',
      navigator.platform || 'unknown',
      randomSeed, // ランダム要素を追加
      canvas.toDataURL()
    ].join('|');
    
    // SHA-256ハッシュの代わりにより強力なハッシュを作成
    let hash = 0;
    for (let i = 0; i < fingerprint.length; i++) {
      const char = fingerprint.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // 32bit整数に変換
    }
    
    const encoded = Math.abs(hash).toString(36) + randomSeed.slice(-8);
    
    if (!encoded || encoded.length < 8) {
      throw new Error('Invalid fingerprint generated');
    }
    
    return encoded.slice(0, 32);
  } catch (error) {
    console.warn('フィンガープリント生成に失敗しました:', error);
    // フォールバック用のランダムID生成
    return 'fb_' + Math.random().toString(36).substr(2, 16) + Date.now().toString(36);
  }
}
