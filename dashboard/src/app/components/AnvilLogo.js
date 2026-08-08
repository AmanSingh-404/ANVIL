export default function AnvilLogo({ size = 'nav' }) {
  const style = size === 'footer' ? { width: '24px', height: '15px' } : {};
  return (
    <svg className="logo-mark" viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg" style={style}>
      <path className="anvil-shine" d="M75,100 Q100,78 125,100 L120,113 Q100,98 80,113 Z" />
      <polygon className="anvil-body" points="10,50 20,36 44,24 186,18 193,29 193,37 168,41 170,58 191,87 185,113 118,113 100,90 82,113 15,113 9,87 30,58 32,41 32,34" />
      <polygon className="anvil-shine" points="14,44 40,28 40,32 18,47" />
      <polygon className="anvil-shine" points="46,23 184,19 184,22 46,26" />
    </svg>
  );
}