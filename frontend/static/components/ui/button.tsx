import React from "react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  size?: "sm" | "md" | "lg";
  variant?: "outline" | "solid";
}

export const Button: React.FC<ButtonProps> = ({
  size = "md",
  variant = "solid",
  className,
  children,
  ...props
}) => {
  const baseStyles = "rounded px-4 py-2 font-medium focus:outline-none";
  const sizeStyles = {
    sm: "text-sm",
    md: "text-base",
    lg: "text-lg px-6 py-3",
  };
  const variantStyles = {
    solid: "bg-blue-600 text-white hover:bg-blue-700",
    outline: "border border-blue-600 text-blue-600 hover:bg-blue-100",
  };

  return (
    <button
      className={`${baseStyles} ${sizeStyles[size]} ${variantStyles[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};