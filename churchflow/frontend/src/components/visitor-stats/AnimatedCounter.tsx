/**
 * Animated Counter Component
 *
 * Displays a number with smooth count-up animation using Framer Motion.
 * Provides a polished, dynamic feel to stat displays.
 */

import { useEffect } from 'react';
import { useMotionValue, useTransform, animate, motion } from 'framer-motion';

interface AnimatedCounterProps {
  value: number;
  className?: string;
  decimals?: number;
}

export default function AnimatedCounter({
  value,
  className = '',
  decimals = 0,
}: AnimatedCounterProps) {
  const motionValue = useMotionValue(0);
  const rounded = useTransform(
    motionValue,
    (latest) => decimals > 0 ? latest.toFixed(decimals) : Math.round(latest).toString()
  );

  useEffect(() => {
    const controls = animate(motionValue, value, {
      duration: 1.2,
      ease: [0.4, 0, 0.2, 1], // Custom cubic-bezier for smooth easing
    });

    return () => controls.stop();
  }, [value, motionValue]);

  return (
    <motion.span
      className={`font-[tabular-nums] ${className}`}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      {rounded}
    </motion.span>
  );
}
