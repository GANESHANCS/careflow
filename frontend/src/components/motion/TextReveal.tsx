import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';

export interface TextRevealProps {
  text: string;
  className?: string;
  variant?: 'fade-slide' | 'word-stagger' | 'line-reveal';
  delay?: number;
  staggerDuration?: number;
  as?: 'h1' | 'h2' | 'h3' | 'h4' | 'p' | 'span' | 'div';
}

export const TextReveal: React.FC<TextRevealProps> = ({
  text,
  className = '',
  variant = 'fade-slide',
  delay = 0,
  staggerDuration = 0.05,
  as: Component = 'span',
}) => {
  const shouldReduceMotion = useReducedMotion();

  if (shouldReduceMotion) {
    return <Component className={className}>{text}</Component>;
  }

  if (variant === 'word-stagger') {
    const words = text.split(' ');
    const containerVariants = {
      hidden: { opacity: 0 },
      show: {
        opacity: 1,
        transition: {
          staggerChildren: staggerDuration,
          delayChildren: delay,
        },
      },
    };

    const wordVariants = {
      hidden: { opacity: 0, y: 12, filter: 'blur(4px)' },
      show: {
        opacity: 1,
        y: 0,
        filter: 'blur(0px)',
        transition: {
          duration: 0.45,
          ease: [0.16, 1, 0.3, 1] as const,
        },
      },
    };

    return (
      <motion.span
        variants={containerVariants}
        initial="hidden"
        whileInView="show"
        viewport={{ once: true, margin: '-20px' }}
        className={`inline-flex flex-wrap gap-x-[0.25em] ${className}`}
      >
        {words.map((word, i) => (
          <motion.span key={`${word}-${i}`} variants={wordVariants} className="inline-block">
            {word}
          </motion.span>
        ))}
      </motion.span>
    );
  }

  if (variant === 'line-reveal') {
    return (
      <span className={`inline-block overflow-hidden ${className}`}>
        <motion.span
          initial={{ y: '100%', opacity: 0 }}
          whileInView={{ y: 0, opacity: 1 }}
          viewport={{ once: true, margin: '-20px' }}
          transition={{
            duration: 0.55,
            delay,
            ease: [0.16, 1, 0.3, 1],
          }}
          className="inline-block"
        >
          {text}
        </motion.span>
      </span>
    );
  }

  // Default: fade-slide
  return (
    <motion.span
      initial={{ opacity: 0, y: 16, filter: 'blur(3px)' }}
      whileInView={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
      viewport={{ once: true, margin: '-20px' }}
      transition={{
        duration: 0.5,
        delay,
        ease: [0.16, 1, 0.3, 1],
      }}
      className={className}
    >
      {text}
    </motion.span>
  );
};
