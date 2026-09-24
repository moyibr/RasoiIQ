'use client';

import { motion, useMotionTemplate, useMotionValue } from 'framer-motion';
import { MouseEvent } from 'react';

export default function SpotlightCard({ children, className = '' }: { children: React.ReactNode, className?: string }) {
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  function handleMouseMove({ currentTarget, clientX, clientY }: MouseEvent) {
    const { left, top } = currentTarget.getBoundingClientRect();
    mouseX.set(clientX - left);
    mouseY.set(clientY - top);
  }

  return (
    <div
      className={"relative group overflow-hidden rounded-3xl border border-white/5 bg-[rgba(27,33,43,0.4)] backdrop-blur-2xl " + className}
      onMouseMove={handleMouseMove}
    >
      <motion.div
        className="pointer-events-none absolute -inset-px rounded-3xl opacity-0 transition duration-300 group-hover:opacity-100"
        style={{
          background: useMotionTemplate`radial-gradient(650px circle at ${mouseX}px ${mouseY}px, rgba(232, 163, 61, 0.1), transparent 80%)`,
        }}
      />
      <motion.div
        className="pointer-events-none absolute -inset-px rounded-3xl opacity-0 transition duration-300 group-hover:opacity-100"
        style={{
          background: useMotionTemplate`radial-gradient(400px circle at ${mouseX}px ${mouseY}px, rgba(255, 255, 255, 0.05), transparent 40%)`,
          zIndex: 1,
        }}
      />
      <div className="relative z-10">{children}</div>
    </div>
  );
}
