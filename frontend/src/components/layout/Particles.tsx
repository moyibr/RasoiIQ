'use client';

import { useEffect, useState } from 'react';

export default function Particles() {
  const [particles, setParticles] = useState<Array<{ id: number, left: string, animationDuration: string, delay: string, size: string }>>([]);

  useEffect(() => {
    const newParticles = Array.from({ length: 40 }).map((_, i) => ({
      id: i,
      left: Math.random() * 100 + '%',
      animationDuration: (15 + Math.random() * 20) + 's',
      delay: '-' + (Math.random() * 20) + 's',
      size: (1 + Math.random() * 3) + 'px'
    }));
    setParticles(newParticles);
  }, []);

  return (
    <div className="particles-bg">
      {particles.map((p) => (
        <div
          key={p.id}
          className="particle"
          style={{
            left: p.left,
            width: p.size,
            height: p.size,
            animationDuration: p.animationDuration,
            animationDelay: p.delay,
          }}
        />
      ))}
    </div>
  );
}
