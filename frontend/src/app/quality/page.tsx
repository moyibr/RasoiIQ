'use client';

import { useState } from 'react';
import { Camera, UploadCloud, AlertTriangle, CheckCircle, Info } from 'lucide-react';
import { api } from '@/lib/api';

export default function QualityCheckPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [surplusId, setSurplusId] = useState<string>('');

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreview(URL.createObjectURL(file));
      setResult(null);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;
    setLoading(true);
    try {
      const res = await api.analyzeQuality(selectedFile, surplusId ? parseInt(surplusId) : undefined);
      setResult(res);
    } catch (err) {
      console.error(err);
      alert('Analysis failed. Make sure backend is running and image is valid.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-5xl mx-auto space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-display font-bold text-white glow-text-primary">Quality Check</h1>
        <p className="text-content-secondary mt-2">Computer Vision analysis for food freshness and spoilage detection.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="glass-premium p-6 rounded-3xl border border-white/5 space-y-6">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Camera size={20} className="text-accent-primary" /> Image Upload
          </h2>
          
          <div className="border-2 border-dashed border-white/10 rounded-2xl p-8 flex flex-col items-center justify-center text-center bg-white/5 hover:bg-white/10 transition-colors cursor-pointer relative">
            <input 
              type="file" 
              accept="image/*"
              onChange={handleFileChange} 
              className="absolute inset-0 opacity-0 cursor-pointer"
            />
            {preview ? (
              <img src={preview} alt="Preview" className="max-h-64 rounded-xl object-contain" />
            ) : (
              <>
                <UploadCloud size={48} className="text-content-secondary mb-4" />
                <p className="text-white font-medium">Click or drag image to upload</p>
                <p className="text-content-secondary text-sm mt-1">Supports JPG, PNG</p>
              </>
            )}
          </div>

          <div>
            <label className="block text-sm text-content-secondary mb-2">Optional: Link to Surplus Event ID</label>
            <input 
              type="number" 
              value={surplusId} 
              onChange={(e) => setSurplusId(e.target.value)}
              placeholder="e.g. 102"
              className="w-full bg-black/30 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-accent-primary"
            />
          </div>

          <button 
            onClick={handleAnalyze} 
            disabled={!selectedFile || loading}
            className="w-full bg-accent-primary hover:bg-accent-primary/90 text-white font-bold py-3 px-6 rounded-xl transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Analyzing...' : 'Analyze Quality'}
          </button>
        </div>

        {result && (
          <div className="glass-premium p-6 rounded-3xl border border-white/5 space-y-6 animate-slide-up">
            <h2 className="text-xl font-bold text-white">Analysis Result</h2>
            
            <div className="flex items-center gap-6 p-6 rounded-2xl bg-black/30 border border-white/5">
              <div className="relative w-24 h-24 flex items-center justify-center">
                <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                  <circle cx="50" cy="50" r="45" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="10" />
                  <circle 
                    cx="50" cy="50" r="45" fill="none" 
                    stroke={result.score > 75 ? '#5fae6e' : result.score > 40 ? '#e8a33d' : '#d9564a'} 
                    strokeWidth="10" strokeDasharray={`${result.score * 2.83} 283`}
                    className="transition-all duration-1000 ease-out"
                  />
                </svg>
                <div className="absolute flex flex-col items-center">
                  <span className="text-2xl font-bold text-white">{result.score}</span>
                  <span className="text-[10px] text-content-secondary uppercase">Score</span>
                </div>
              </div>
              
              <div className="flex-1 space-y-2">
                <div className="flex items-center gap-2">
                  {result.category === 'Fresh' ? <CheckCircle className="text-status-success" /> : <AlertTriangle className={result.category === 'Spoiled' ? 'text-status-critical' : 'text-status-warning'} />}
                  <span className="text-xl font-bold text-white">{result.category}</span>
                </div>
                <p className="text-content-secondary text-sm">{result.reason}</p>
              </div>
            </div>

            <div className="p-4 rounded-xl bg-accent-primary/10 border border-accent-primary/20 flex gap-3 text-sm">
              <Info className="text-accent-primary shrink-0" size={20} />
              <p className="text-content-secondary">
                {result.updated_surplus_id 
                  ? `Surplus Event #${result.updated_surplus_id} has been automatically updated based on this quality check.`
                  : 'Image analyzed successfully. No surplus event was linked.'}
              </p>
            </div>
            
            {!result.updated_surplus_id && result.category !== 'Spoiled' && (
              <button className="w-full bg-white/10 hover:bg-white/20 text-white font-medium py-3 px-6 rounded-xl transition-all">
                Add as New Surplus
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
