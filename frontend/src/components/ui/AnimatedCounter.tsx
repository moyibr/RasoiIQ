'use client';

import { useEffect, useState } from 'react';
import { motion, useSpring, useTransform } from 'framer-motion';

export default function AnimatedCounter({ value, prefix = '', suffix = '' }: { value: number, prefix?: string, suffix?: string }) {
  const [hasMounted, setHasMounted] = useState(false);
  const spring = useSpring(0, { mass: 1, stiffness: 50, damping: 20 });
  const display = useTransform(spring, (current) => 
    Math.round(current).toLocaleString('en-IN')
  );

  useEffect(() => {
    setHasMounted(true);
    spring.set(value);
  }, [value, spring]);

  if (!hasMounted) {
    return <span>{prefix}{value.toLocaleString('en-IN')}{suffix}</span>;
  }

  return (
    <span className="inline-flex">
      {prefix && <span>{prefix}</span>}
      <motion.span>{display}</motion.span>
      {suffix && <span>{suffix}</span>}
    </span>
  );
}
