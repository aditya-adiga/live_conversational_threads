import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

export default function AuthButton() {
  const { currentUser, signOut } = useAuth();
  const navigate = useNavigate();

  const handleAuth = async () => {
    if (currentUser) {
      try {
        await signOut();
        navigate('/');
      } catch (error) {
        console.error('Sign out error:', error);
      }
    } else {
      navigate('/login');
    }
  };

  // Get user initials from display name
  const getInitials = (name) => {
    if (!name) return 'U';
    return name
      .split(' ')
      .map(word => word.charAt(0).toUpperCase())
      .join('')
      .slice(0, 2);
  };

  return (
    <button
      onClick={handleAuth}
      className="flex items-center gap-2 px-4 py-2 bg-white/20 hover:bg-white/30 backdrop-blur-sm text-white rounded-xl transition-all duration-200 border border-white/30 hover:border-white/40"
    >
      {currentUser ? (
        <>
          {currentUser.photoURL ? (
            <img 
              src={currentUser.photoURL} 
              alt="Profile"
              className="w-6 h-6 rounded-full border border-white/40"
              crossOrigin="anonymous"
              referrerPolicy="no-referrer"
              onError={(e) => {
                console.log('Profile image failed to load:', currentUser.photoURL);
                
                // Try fetching the URL to see the actual error
                fetch(currentUser.photoURL, { mode: 'no-cors' })
                  .then(() => console.log('Fetch successful - likely CORS issue'))
                  .catch(err => console.log('Fetch failed:', err));
                
                e.target.style.display = 'none';
                e.target.nextSibling.style.display = 'flex';
              }}
            />
          ) : null}
          <div 
            className="w-6 h-6 rounded-full bg-white/30 border border-white/40 flex items-center justify-center text-xs font-bold"
            style={{ display: currentUser.photoURL ? 'none' : 'flex' }}
          >
            {getInitials(currentUser.displayName)}
          </div>
          <span className="font-medium">Sign Out</span>
        </>
      ) : (
        <>
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
          </svg>
          <span className="font-medium">Sign In</span>
        </>
      )}
    </button>
  );
}
