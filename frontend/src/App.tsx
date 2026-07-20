import { useEffect, useState } from 'react';
import { getHello } from './ecommerceAPP/hello';

function App() {
  const [message, setMessage] = useState<string>('Loading...');

  useEffect(() => {
    getHello()
      .then((data) => setMessage(data.message))
      .catch((error) => {
        console.error('API error:', error);
        setMessage('Failed to fetch from backend');
      });
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
      <div className="bg-white shadow-xl rounded-2xl p-10 text-center max-w-md w-full">
        <h1 className="text-4xl font-bold text-gray-800 mb-4">
          Django + React
        </h1>

        <p className="text-lg text-blue-600 font-medium">
          {message}
        </p>
      </div>
    </div>
  );
}

export default App;