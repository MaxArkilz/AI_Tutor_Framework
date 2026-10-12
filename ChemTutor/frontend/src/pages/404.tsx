export default function NotFound() {
  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center', 
      justifyContent: 'center', 
      height: '60vh',
      gap: '1rem',
      textAlign: 'center'
    }}>
      <h1 style={{ fontSize: '4rem', fontWeight: 700, color: '#002E5D', margin: 0 }}>404</h1>
      <p style={{ fontSize: '1.25rem', color: '#4d5056' }}>Page not found</p>
      <a href="/" style={{ color: '#002E5D', textDecoration: 'underline' }}>Go home</a>
    </div>
  );
}