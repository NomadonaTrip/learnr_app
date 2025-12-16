interface FooterLink {
  label: string
  href: string
}

const footerLinks: FooterLink[] = [
  { label: 'About', href: '/about' },
  { label: 'Privacy Policy', href: '/privacy' },
  { label: 'Terms of Service', href: '/terms' },
  { label: 'Contact', href: '/contact' },
]

/**
 * Footer component with standard links and copyright notice.
 * Responsive layout with accessible link styling.
 */
export function Footer() {
  const currentYear = new Date().getFullYear()

  return (
    <footer
      className="px-4 sm:px-6 lg:px-8 py-8 border-t border-charcoal/10 bg-cream"
      role="contentinfo"
    >
      <div className="mx-auto max-w-content">
        <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
          {/* Copyright */}
          <p className="text-charcoal/60 text-sm">
            &copy; {currentYear} LearnR. All rights reserved.
          </p>

          {/* Links */}
          <nav aria-label="Footer navigation">
            <ul className="flex flex-wrap justify-center gap-x-6 gap-y-2">
              {footerLinks.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    className="text-charcoal/60 hover:text-charcoal text-sm transition-colors duration-200
                      focus:outline-none focus-visible:ring-2 focus-visible:ring-primary-500 focus-visible:ring-offset-2 rounded"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </nav>
        </div>
      </div>
    </footer>
  )
}

export default Footer
