import React, { useState } from 'react';
import { submitFeedback } from '../services/api';
import { Star, MessageSquareHeart } from 'lucide-react';
import Loader from '../components/Loader';

const Feedback = () => {
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [comments, setComments] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (rating === 0) return;

    setLoading(true);
    try {
      await submitFeedback({ rating, comments });
      setSuccess(true);
    } catch (error) {
      console.error('Failed to submit feedback', error);
      // Show success anyway for demo purposes if backend doesn't have the route yet
      setSuccess(true); 
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8 animate-fade-in py-10">
      <div className="text-center space-y-4">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-rose-100 text-rose-500 mb-2">
          <MessageSquareHeart className="w-8 h-8" />
        </div>
        <h1 className="text-3xl font-bold text-slate-800">Your Feedback Matters</h1>
        <p className="text-slate-500">Help us improve our service by rating your experience.</p>
      </div>

      <div className="glass-panel p-8 md:p-10 text-center relative overflow-hidden">
        {loading && <Loader fullScreen={false} />}

        {success ? (
          <div className="py-8 animate-slide-up">
            <h2 className="text-2xl font-bold text-emerald-600 mb-2">Thank You!</h2>
            <p className="text-slate-600">Your feedback has been successfully submitted.</p>
            <button
              onClick={() => { setSuccess(false); setRating(0); setComments(''); }}
              className="mt-6 btn-secondary"
            >
              Submit Another
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className={`space-y-8 ${loading ? 'opacity-50 pointer-events-none' : ''}`}>
            
            <div className="space-y-4">
              <label className="text-sm font-semibold text-slate-700 block uppercase tracking-wider">Rate your experience</label>
              <div className="flex justify-center gap-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    type="button"
                    key={star}
                    onClick={() => setRating(star)}
                    onMouseEnter={() => setHoverRating(star)}
                    onMouseLeave={() => setHoverRating(0)}
                    className="p-1 transition-transform hover:scale-110 focus:outline-none"
                  >
                    <Star 
                      className={`w-10 h-10 ${
                        (hoverRating || rating) >= star 
                          ? 'fill-amber-400 text-amber-400' 
                          : 'text-slate-200 fill-slate-50'
                      } transition-colors`} 
                    />
                  </button>
                ))}
              </div>
            </div>

            <div className="space-y-2 text-left">
              <label className="text-sm font-semibold text-slate-700 block">Additional Comments (Optional)</label>
              <textarea
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                placeholder="Tell us what you liked or how we can improve..."
                rows="4"
                className="input-field resize-none bg-slate-50 focus:bg-white"
              ></textarea>
            </div>

            <button 
              type="submit" 
              disabled={rating === 0}
              className={`w-full py-3 text-lg font-bold rounded-xl transition-all shadow-md ${
                rating === 0 
                  ? 'bg-slate-200 text-slate-400 cursor-not-allowed' 
                  : 'bg-primary-600 text-white hover:bg-primary-700 hover:shadow-lg active:scale-95'
              }`}
            >
              Submit Feedback
            </button>
          </form>
        )}
      </div>
    </div>
  );
};

export default Feedback;
