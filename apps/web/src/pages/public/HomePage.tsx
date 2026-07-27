import { motion } from "framer-motion";
import { Link } from "react-router";

import { Button } from "@/components/ui/button";
import { login } from "@/lib/auth/keycloak";

export function HomePage() {
  return (
    <section className="relative overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_#1f6b4f_0%,_transparent_55%),linear-gradient(160deg,#071a14_0%,#0b3d2e_45%,#1f6b4f_100%)]" />
      <div className="absolute inset-0 opacity-30 [background-image:radial-gradient(circle_at_1px_1px,rgba(200,245,96,0.35)_1px,transparent_0)] [background-size:28px_28px]" />

      <div className="relative mx-auto flex min-h-[calc(100dvh-5rem)] max-w-6xl flex-col justify-end px-5 pb-16 pt-10 text-sand md:justify-center md:pb-24">
        <motion.p
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="font-display text-5xl font-extrabold tracking-tight text-lime sm:text-7xl md:text-8xl"
        >
          TetherFit
        </motion.p>
        <motion.h1
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.08 }}
          className="mt-4 max-w-2xl font-display text-3xl font-bold leading-tight sm:text-4xl"
        >
          Run your coaching business from one calm OS.
        </motion.h1>
        <motion.p
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.16 }}
          className="mt-4 max-w-xl text-base text-sand/80 sm:text-lg"
        >
          Clients, sessions, workouts, and payments — built for solo trainers and small studios.
        </motion.p>
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, delay: 0.24 }}
          className="mt-8 flex flex-wrap gap-3"
        >
          <Button size="lg" onClick={() => void login()}>
            Start free
          </Button>
          <Link to="/features">
            <Button size="lg" variant="outline" className="border-sand/30 bg-white/5 text-sand">
              See features
            </Button>
          </Link>
        </motion.div>
      </div>
    </section>
  );
}
