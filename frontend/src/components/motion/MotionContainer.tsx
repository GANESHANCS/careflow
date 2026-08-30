import React from 'react';
import { motion, type HTMLMotionProps } from 'framer-motion';

export interface MotionContainerProps extends HTMLMotionProps<'div'> {
  stagger?: number;
  delay?: number;
}

export const MotionContainer: React.FC<MotionContainerProps> = ({
  children,
  stagger = 0.08,
  delay = 0,
  className,
  ...props
}) => {
  return (
    <motion.div
      initial="hidden"
      animate="show"
      exit="exit"
      variants={{
        hidden: { opacity: 0 },
        show: {
          opacity: 1,
          transition: {
            staggerChildren: stagger,
            delayChildren: delay,
          },
        },
        exit: { opacity: 0 },
      }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  );
};

export const MotionItem: React.FC<HTMLMotionProps<'div'>> = ({ children, className, ...props }) => {
  return (
    <motion.div
      variants={{
        hidden: { opacity: 0, y: 12 },
        show: { opacity: 1, y: 0, transition: { duration: 0.35, ease: [0.16, 1, 0.3, 1] } },
        exit: { opacity: 0, y: -8 },
      }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  );
};
